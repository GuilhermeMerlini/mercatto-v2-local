"""Harness: monta o prompt, chama o LLM local, grava os arquivos, roda os testes e repete.

Uso: python harness/run.py 3                      (issue 03 em docs/issues/)
     python harness/run.py 3 --model qwen3.6:35b --continue
     python harness/run.py 6 --continue --hint "o total de list_products ignora o filtro"
     python harness/run.py docs/issues/03-users-register-login.md
     python harness/run.py 1 --register-ci             (só registra os testes no CI, sem chamar o modelo)
Quando a issue passa, os arquivos de teste dela vão para .github/ci-tests.txt.
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
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("LLM_API_KEY", "local"),
)

SYSTEM = """Você é um engenheiro de software. Resolva SOMENTE a issue pedida,
respeitando a ARQUITETURA fornecida. Responda apenas com blocos nos formatos abaixo, sem explicações.

Arquivo novo, ou reescrito por inteiro:
### FILE: caminho/relativo/arquivo.ext
```
conteúdo completo
```

Mudança pontual em arquivo que já existe (prefira este formato ao corrigir erros):
### EDIT: caminho/relativo/arquivo.ext
<<<<<<< SEARCH
linhas atuais, copiadas exatamente do arquivo
=======
linhas novas
>>>>>>> REPLACE

Um EDIT pode ter vários pares SEARCH/REPLACE. O trecho do SEARCH precisa aparecer uma única vez
no arquivo: inclua linhas vizinhas se precisar. REPLACE vazio apaga o trecho."""

HEADER_RE = re.compile(r"^### (FILE|EDIT): (.+?)[ \t]*$", re.MULTILINE)
EDIT_RE = re.compile(
    r"^<{5,9} ?SEARCH[ \t]*\n(.*?)^={5,9}[ \t]*\n(.*?)^>{5,9} ?REPLACE[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def _strip_fences(body: str) -> str:
    lines = body.strip("\n").split("\n")
    if lines and lines[0].lstrip().startswith("```"):
        lines = lines[1:]  # cerca de abertura
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]  # cerca de fechamento
    return "\n".join(lines)


def parse_blocks(reply: str):
    """Extrai [(tipo, caminho, corpo)] da resposta, com tipo FILE ou EDIT.
    No FILE, o corpo é o conteúdo sem as cercas (tolera arquivos vazios, ex.: __init__.py);
    no EDIT, é uma lista de pares (search, replace)."""
    parts = HEADER_RE.split(reply)  # [antes, tipo1, caminho1, corpo1, tipo2, ...]
    out = []
    for kind, path, body in zip(parts[1::3], parts[2::3], parts[3::3]):
        if kind == "FILE":
            out.append((kind, path.strip(), _strip_fences(body)))
        else:
            out.append((kind, path.strip(), EDIT_RE.findall(body)))
    return out


def apply_edit(content: str, search: str, replace: str):
    """Aplica um par SEARCH/REPLACE. Devolve (novo conteúdo, None) ou (None, motivo da falha).
    Tenta o texto exato; se não achar, compara linha a linha ignorando espaços no fim das linhas."""
    if not search.strip():
        return None, "SEARCH vazio"
    count = content.count(search)
    if count == 1:
        return content.replace(search, replace), None
    if count > 1:
        return None, f"SEARCH aparece {count} vezes; inclua linhas vizinhas para ficar único"
    lines = content.split("\n")
    want = [s.rstrip() for s in search.strip("\n").split("\n")]
    hits = [i for i in range(len(lines) - len(want) + 1)
            if [s.rstrip() for s in lines[i:i + len(want)]] == want]
    if len(hits) != 1:
        return None, ("SEARCH não encontrado no arquivo" if not hits
                      else f"SEARCH aparece {len(hits)} vezes; inclua linhas vizinhas para ficar único")
    i = hits[0]
    new = replace.strip("\n").split("\n") if replace.strip("\n") else []
    return "\n".join(lines[:i] + new + lines[i + len(want):]), None


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


SEARCH_MARK_RE = re.compile(r"^<{5,9} ?SEARCH[ \t]*$|^>{5,9} ?REPLACE[ \t]*$", re.MULTILINE)


def apply_files(reply: str):
    """Grava os blocos FILE e aplica os EDIT. Devolve (arquivos alterados, erros dos EDIT)
    e os erros são [(caminho, motivo)]. Os pares de um EDIT que batem são aplicados mesmo se
    outro par do mesmo arquivo falhar."""
    written, errors = [], []
    for kind, rel, body in parse_blocks(reply):
        target = (ROOT / rel).resolve()
        if ROOT not in target.parents:  # nunca escrever fora do projeto
            continue
        if is_protected(target.relative_to(ROOT).as_posix()):  # testes e gerados
            continue
        if kind == "FILE":
            if SEARCH_MARK_RE.search(body):  # bloco EDIT com cabeçalho de FILE: gravaria os marcadores
                errors.append((rel, "### FILE com marcadores <<<<<<< SEARCH / >>>>>>> REPLACE; o arquivo NÃO "
                                    "foi gravado. Use ### EDIT para mudanças pontuais, ou ### FILE com o "
                                    "conteúdo completo, sem marcadores"))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body + "\n" if body else "")
            written.append(rel)
            continue
        if not target.exists():
            errors.append((rel, "EDIT em arquivo que não existe; use ### FILE para criar"))
            continue
        if not body:
            errors.append((rel, "EDIT sem nenhum par <<<<<<< SEARCH / ======= / >>>>>>> REPLACE válido"))
            continue
        content, changed = target.read_text(), False
        for n, (search, replace) in enumerate(body, 1):
            new, err = apply_edit(content, search, replace)
            if err:
                errors.append((rel, f"par {n}: {err}"))
            else:
                content, changed = new, True
        if changed:
            target.write_text(content if content.endswith("\n") else content + "\n")
            written.append(rel)
    return written, errors


def edit_feedback(errors) -> str:
    """Mensagem para o modelo sobre os EDIT que falharam, com o conteúdo atual dos arquivos."""
    if not errors:
        return ""
    msgs = "\n".join(f"- {rel}: {err}" for rel, err in errors)
    files = read_files(sorted({rel for rel, _ in errors if (ROOT / rel).exists()}))
    return (f"Alguns blocos FILE/EDIT não foram aplicados:\n{msgs}\n"
            f"Conteúdo atual desses arquivos (copie o SEARCH exatamente daqui):\n{files}\n\n")


SUMMARY_MARK = "short test summary info"


def run_tests(cmd, budget=6000):
    """Roda os testes e devolve (passou, saída limitada a ~budget chars).

    No pytest, mostra até 8 falhas (não só a 1ª) com traceback curto e sem warnings, e `-rf` lista
    TODAS as falhas no resumo final. Se a saída passar do budget, o resumo é mantido inteiro e
    o resto do espaço vai para os tracebacks do início (as primeiras falhas).
    """
    if "pytest" in cmd:
        cmd += " --maxfail=8 --tb=short -p no:warnings -rf"
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=300)
    out = r.stdout + r.stderr
    if len(out) > budget:
        idx = out.rfind(SUMMARY_MARK)
        if idx == -1:  # sem resumo do pytest (erro de coleta, outro comando): fica o fim do log
            out = out[-budget:]
        else:
            line_start = out.rfind("\n", 0, idx) + 1  # inclui a linha "=== short test summary ==="
            head, summary = out[:line_start], out[line_start:]
            out = head[: max(budget - len(summary), 0)] + "\n[... saída cortada ...]\n" + summary
    return r.returncode == 0, out


CI_TESTS = ROOT / ".github/ci-tests.txt"
TEST_FILE_RE = re.compile(r"\btests/test_\w+\.py\b")


def register_ci_tests(meta) -> None:
    """Acrescenta em .github/ci-tests.txt os arquivos de teste do backend desta issue que passam inteiros.

    Candidatos: os arquivos citados no test_cmd + o tests/test_issue_NN_*.py da própria issue.
    Cada um é rodado sozinho e sem filtro: issues que testam só parte de um arquivo (03a/03b, com -k)
    não registram o arquivo enquanto a outra parte ainda falha.
    """
    candidates = set(TEST_FILE_RE.findall(meta["test_cmd"]))
    num = re.match(r"\d+", meta["id"])
    if num:
        candidates |= {p.relative_to(ROOT / "backend").as_posix()
                       for p in (ROOT / "backend/tests").glob(f"test_issue_{int(num.group()):02d}_*.py")}
    if not candidates:
        return
    listed = {line.strip() for line in CI_TESTS.read_text().splitlines()} if CI_TESTS.exists() else set()
    added = []
    for rel in sorted(candidates - listed):
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:warnings", rel],
                           cwd=ROOT / "backend", capture_output=True, text=True, timeout=300, check=False)
        if r.returncode == 0:
            added.append(rel)
        else:
            print(f"[{meta['id']}] CI: {rel} ainda não passa inteiro; não registrado.", flush=True)
    if added:
        with open(CI_TESTS, "a") as f:
            f.writelines(rel + "\n" for rel in added)
        print(f"[{meta['id']}] CI: registrado em .github/ci-tests.txt: {added}", flush=True)


def run_issue(issue_path: Path, model: str, resume: bool = False, hint: str | None = None):
    meta, body = load_issue(issue_path)
    prompt = build_prompt(meta, body)
    if resume:
        ok, output = run_tests(meta["test_cmd"])
        if ok:
            print(f"[{meta['id']}] os testes já passam; nada a continuar.")
            register_ci_tests(meta)
            return
        work = current_work_files(exclude=meta.get("context_files", []))
        print(f"[{meta['id']}] retomando com {len(work)} arquivo(s) existente(s): {work}", flush=True)
        prompt += (
            f"\n\n# TRABALHO ANTERIOR (continue a partir daqui)\n{read_files(work)}\n\n"
            f"# SAÍDA ATUAL DOS TESTES\n{output}\n\n"
            "Corrija ou complete o que falta. Para arquivos que já existem, prefira blocos EDIT."
        )
    if hint:
        prompt += f"\n\n# INSTRUÇÃO EXTRA (siga com prioridade)\n{hint.strip()}"
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]
    log = {
        "issue": meta["id"], "model": model, "iters": 0, "passed": False, "resumed": resume, "hint": bool(hint),
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
        files, edit_errors = apply_files(reply)
        print(f"[{meta['id']}] tentativa {i}/{meta.get('max_iters', 4)} "
              f"({round(time.time() - t0)}s) arquivos escritos: {files or 'NENHUM'}", flush=True)
        for rel, err in edit_errors:
            print(f"    EDIT falhou em {rel}: {err}", flush=True)
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
                "content": f"{edit_feedback(edit_errors)}"
                f"Os testes falharam. Arquivos alterados: {files}\n"
                f"Saída:\n{output}\nCorrija com blocos EDIT (ou FILE para arquivos novos).",
            },
        ]

    log["seconds"] = round(time.time() - t0, 1)
    with open(ROOT / "docs/results.jsonl", "a") as f:
        f.write(json.dumps(log) + "\n")
    print(log)
    if log["passed"]:
        register_ci_tests(meta)


def register_only(issue_path: Path) -> None:
    """Para issues corrigidas à mão: confere o test_cmd e registra os testes no CI, sem chamar o modelo."""
    meta, _ = load_issue(issue_path)
    ok, output = run_tests(meta["test_cmd"])
    if not ok:
        sys.exit(f"[{meta['id']}] os testes não passam; nada registrado.\n{output}")
    register_ci_tests(meta)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("issue", help="número da issue (ex.: 3) ou caminho do .md")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="ex.: qwen3:8b ou qwen3.6:35b")
    ap.add_argument("--continue", dest="resume", action="store_true",
                    help="continua a partir dos arquivos e do erro da tentativa anterior (sem reset)")
    ap.add_argument("--hint", help="instrução extra acrescentada ao fim do prompt "
                    "(ex.: o que corrigir). Texto longo: --hint \"$(cat dica.txt)\"")
    ap.add_argument("--register-ci", action="store_true",
                    help="não chama o modelo: só confere os testes e registra a issue em "
                         ".github/ci-tests.txt (para issues corrigidas à mão)")
    args = ap.parse_args()
    if args.register_ci:
        register_only(resolve_issue(args.issue))
    else:
        run_issue(resolve_issue(args.issue), args.model, args.resume, args.hint)
