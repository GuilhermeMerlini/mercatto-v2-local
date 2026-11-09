"""Harness: monta o prompt, chama o LLM local, grava os arquivos, roda os testes e repete.

Uso: python harness/run.py docs/tasks/01-core-users.md --model qwen3:8b
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

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen3:8b")
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("LLM_API_KEY", "local"),
)

SYSTEM = """Você é um engenheiro de software. Implemente SOMENTE a tarefa pedida,
respeitando a ARQUITETURA fornecida. Responda apenas com arquivos completos neste formato,
sem explicações:
### FILE: caminho/relativo/arquivo.ext
```
conteúdo completo
```"""

FILE_RE = re.compile(r"### FILE: (.+?)\n```[^\n]*\n(.*?)\n```", re.S)


def load_task(path: Path):
    _, front, body = path.read_text().split("---", 2)
    return yaml.safe_load(front), body.strip()


def read_files(paths):
    out = []
    for p in paths:
        f = ROOT / p
        if f.exists():
            out.append(f"### FILE: {p}\n```\n{f.read_text()}\n```")
    return "\n\n".join(out)


def build_prompt(meta, body):
    return (
        f"# ARQUITETURA\n{(ROOT / 'docs/ARCHITECTURE.md').read_text()}\n\n"
        f"# TAREFA\n{body}\n\n"
        f"# ARQUIVOS EXISTENTES RELEVANTES\n{read_files(meta.get('context_files', []))}"
    )


def apply_files(reply: str):
    written = []
    for rel, content in FILE_RE.findall(reply):
        target = (ROOT / rel.strip()).resolve()
        if ROOT not in target.parents:  # nunca escrever fora do projeto
            continue
        if (ROOT / "backend/tests") in target.parents:  # o modelo não altera os testes
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content + "\n")
        written.append(rel.strip())
    return written


def run_tests(cmd):
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=300)
    return r.returncode == 0, (r.stdout + r.stderr)[-4000:]  # só o fim do log


def run_task(task_path: Path, model: str):
    meta, body = load_task(task_path)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": build_prompt(meta, body)},
    ]
    log = {
        "task": meta["id"], "model": model, "iters": 0, "passed": False,
        "prompt_tokens": 0, "completion_tokens": 0, "ts": int(time.time()),
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
    ap.add_argument("task", type=Path)
    ap.add_argument("--model", default=DEFAULT_MODEL, help="ex.: qwen3:8b ou qwen3.6:35b")
    args = ap.parse_args()
    run_task(args.task, args.model)
