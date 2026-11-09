"""Harness: monta o prompt, chama o LLM local, grava os arquivos, roda os testes e repete.

Uso: python harness/run.py 3                      (issue 03 em docs/issues/)
     python harness/run.py 3 --model qwen3.6:35b --continue
     python harness/run.py docs/issues/03-users-register-login.md
Config por env: LLM_BASE_URL, LLM_MODEL (padrão), LLM_API_KEY, LLM_TEMPERATURE
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml
from openai import OpenAI
from signatures import signatures

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen3:8b")
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("LLM_API_KEY", "local"),
)

SYSTEM = """Você é um engenheiro de software. Resolva SOMENTE a issue pedida,
respeitando a ARQUITETURA fornecida. Responda apenas com arquivos completos neste formato,
sem explicações:
### FILE: caminho/relativo/arquivo.ext
```
conteúdo completo
```"""

HEADER_RE = re.compile(r"^### FILE: (.+?)[ \t]*$", re.M)


def parse_files(reply: str):
    """Extrai [(caminho, conteúdo)] da resposta. Tolera arquivos vazios (ex.: __init__.py)."""
    parts = HEADER_RE.split(reply)  # [antes, caminho1, corpo1, caminho2, corpo2, ...]
    out = []
    for path, body in zip(parts[1::2], parts[2::2]):
        lines = body.strip("\n").split("\n")
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]  # cerca de abertura
        while lines and not lines[-1].strip():
            lines.pop()
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # cerca de fechamento
        out.append((path.strip(), "\n".join(lines)))
    return out


# O modelo nunca escreve aqui: testes (escritos por humanos) e arquivos gerados.
PROTECTED_DIRS = ("backend/tests", "frontend/src/__tests__", "frontend/node_modules")
PROTECTED_FILES = ("frontend/src/api/schema.d.ts", "frontend/openapi.json", "frontend/package-lock.json")
WORK_EXTENSIONS = (".py", ".ts", ".tsx", ".css", ".json", ".html", ".md")


def is_protected(rel: str) -> bool:
    return rel in PROTECTED_FILES or any(rel == d or rel.startswith(d + "/") for d in PROTECTED_DIRS)


def current_work_files(exclude):
    """Código criado/alterado desde o último commit (exceto protegidos e arquivos já no contexto)."""
    r = subprocess.run("git ls-files -m -o --exclude-standard -- backend frontend",
                       shell=True, cwd=ROOT, capture_output=True, text=True)
    return [p for p in r.stdout.splitlines()
            if p.endswith(WORK_EXTENSIONS) and not is_protected(p) and p not in exclude]


def resolve_issue(arg: str) -> Path:
    """Aceita o número da issue (3, 03) ou o caminho do arquivo."""
    if arg.isdigit():
        matches = sorted((ROOT / "docs/issues").glob(f"{int(arg):02d}-*.md"))
        if len(matches) != 1:
            sys.exit(f"Issue {arg}: esperado 1 arquivo em docs/issues/, achei {len(matches)}")
        return matches[0]
    path = Path(arg)
    if not path.exists():
        sys.exit(f"Arquivo não encontrado: {arg}")
    return path


def load_issue(path: Path):
    _, front, body = path.read_text().split("---", 2)
    return yaml.safe_load(front), body.strip()


def read_files(paths):
    out = []
    for p in paths:
        f = ROOT / p
        if f.exists():
            out.append(f"### FILE: {p}\n```\n{f.read_text()}\n```")
    return "\n\n".join(out)


def find_issue(issue_id: str) -> Path:
    path = ROOT / "docs/issues" / f"{issue_id}.md"
    if not path.exists():
        sys.exit(f"depends: issue '{issue_id}' não existe em docs/issues/")
    return path


def dependency_api(meta):
    """Assinaturas dos arquivos `provides` das issues em `depends` (sem o corpo do código).
    Arquivos que já estão em context_files vão inteiros, então ficam de fora daqui."""
    in_context = set(meta.get("context_files", []))
    seen, blocks, missing = set(), [], []
    for dep in meta.get("depends", []):
        dep_meta, _ = load_issue(find_issue(dep))
        for rel in dep_meta.get("provides", []):
            if rel in seen or rel in in_context:
                continue
            seen.add(rel)
            f = ROOT / rel
            if not f.exists():
                missing.append(f"{rel} (issue {dep})")
                continue
            try:
                api = signatures(rel, f.read_text())
            except SyntaxError:
                api = f.read_text()  # arquivo quebrado: melhor mostrar inteiro
            blocks.append(f"### API: {rel}  (de {dep})\n```\n{api}\n```")
    if missing:
        print("AVISO: dependências ainda não implementadas: " + ", ".join(missing), flush=True)
    return "\n\n".join(blocks)


def build_prompt(meta, body):
    prompt = (
        f"# ARQUITETURA\n{(ROOT / 'docs/ARCHITECTURE.md').read_text()}\n\n"
        f"# ISSUE\n{body}\n\n"
    )
    api = dependency_api(meta)
    if api:
        prompt += (
            "# API PÚBLICA DAS DEPENDÊNCIAS\n"
            "Só assinaturas (o corpo foi omitido). Use estas funções e tipos; não reescreva estes "
            "arquivos a menos que a issue peça.\n\n"
            f"{api}\n\n"
        )
    return prompt + f"# ARQUIVOS EXISTENTES RELEVANTES\n{read_files(meta.get('context_files', []))}"


def apply_files(reply: str):
    written = []
    for rel, content in parse_files(reply):
        target = (ROOT / rel).resolve()
        if ROOT not in target.parents:  # nunca escrever fora do projeto
            continue
        if is_protected(target.relative_to(ROOT).as_posix()):  # testes e gerados
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content + "\n" if content else "")
        written.append(rel)
    return written


def run_tests(cmd):
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=300)
    return r.returncode == 0, (r.stdout + r.stderr)[-4000:]  # só o fim do log


def run_issue(issue_path: Path, model: str, resume: bool = False):
    meta, body = load_issue(issue_path)
    prompt = build_prompt(meta, body)
    if resume:
        ok, output = run_tests(meta["test_cmd"])
        if ok:
            print(f"[{meta['id']}] os testes já passam; nada a continuar.")
            return
        work = current_work_files(exclude=meta.get("context_files", []))
        print(f"[{meta['id']}] retomando com {len(work)} arquivo(s) existente(s): {work}", flush=True)
        prompt += (
            f"\n\n# TRABALHO ANTERIOR (continue a partir daqui)\n{read_files(work)}\n\n"
            f"# SAÍDA ATUAL DOS TESTES\n{output}\n\n"
            "Corrija ou complete o que falta e devolva os arquivos completos que mudarem."
        )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]
    log = {
        "issue": meta["id"], "model": model, "iters": 0, "passed": False, "resumed": resume,
        "prompt_tokens": 0, "completion_tokens": 0, "prompt_chars": len(prompt), "ts": int(time.time()),
    }
    t0 = time.time()

    for i in range(1, meta.get("max_iters", 4) + 1):
        log["iters"] = i
        print(f"[{meta['id']}] tentativa {i}: aguardando o modelo {model}...", flush=True)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        )
        if resp.usage:
            log["prompt_tokens"] += resp.usage.prompt_tokens
            log["completion_tokens"] += resp.usage.completion_tokens
        # qwen3 pode devolver o raciocínio em <think>...</think>; não faz parte da resposta
        reply = THINK_RE.sub("", resp.choices[0].message.content or "").strip()
        files = apply_files(reply)
        print(f"[{meta['id']}] tentativa {i}/{meta.get('max_iters', 4)} "
              f"({round(time.time() - t0)}s) arquivos escritos: {files or 'NENHUM'}", flush=True)
        ok, output = run_tests(meta["test_cmd"])
        summary = output.strip().splitlines()[-1] if output.strip() else "(sem saída)"
        print(f"    testes: {'PASSOU' if ok else 'FALHOU'} — {summary}", flush=True)
        if ok:
            log["passed"] = True
            break
        messages += [
            {"role": "assistant", "content": reply},
            {
                "role": "user",
                "content": f"Os testes falharam. Arquivos escritos: {files}\n"
                f"Saída:\n{output}\nCorrija e devolva os arquivos completos.",
            },
        ]

    log["seconds"] = round(time.time() - t0, 1)
    with open(ROOT / "docs/results.jsonl", "a") as f:
        f.write(json.dumps(log) + "\n")
    print(log)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("issue", help="número da issue (ex.: 3) ou caminho do .md")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="ex.: qwen3:8b ou qwen3.6:35b")
    ap.add_argument("--continue", dest="resume", action="store_true",
                    help="continua a partir dos arquivos e do erro da tentativa anterior (sem reset)")
    args = ap.parse_args()
    run_issue(resolve_issue(args.issue), args.model, args.resume)
