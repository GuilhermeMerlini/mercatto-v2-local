"""Exporta o OpenAPI do backend sem subir o servidor (usado pelas issues de front).

Uso: python harness/export_openapi.py > frontend/openapi.json
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite://")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402

print(json.dumps(app.openapi(), indent=2, ensure_ascii=False))
