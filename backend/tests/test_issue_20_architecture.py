"""Regras do docs/ARCHITECTURE.md verificadas sobre o código (via ast)."""
import ast
from pathlib import Path

import pytest

MODULES_DIR = Path(__file__).resolve().parent.parent / "app" / "modules"
MODULES = ["users", "catalog", "search", "cart", "orders", "payments", "reviews", "sellers"]
ALLOWED = {
    "users": set(),
    "catalog": {"users"},
    "search": {"catalog"},
    "cart": {"catalog"},
    "orders": {"catalog", "payments"},
    "payments": set(),
    "reviews": {"catalog", "users"},
    "sellers": {"catalog", "orders"},
}


def module_files():
    for module in MODULES:
        for path in sorted((MODULES_DIR / module).glob("*.py")):
            yield module, path


def imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
            # "from app.modules.catalog import service" → app.modules.catalog.service
            found += [f"{node.module}.{a.name}" for a in node.names if node.module.startswith("app.modules")]
        elif isinstance(node, ast.Import):
            found += [a.name for a in node.names]
    return found


def cross_module_imports():
    for module, path in module_files():
        for name in imports(path):
            parts = name.split(".")
            if parts[:2] == ["app", "modules"] and len(parts) >= 3 and parts[2] != module and parts[2] in MODULES:
                yield module, path, name


def test_all_modules_exist():
    for module in MODULES:
        assert (MODULES_DIR / module / "service.py").exists(), f"falta {module}/service.py"


def test_modules_talk_only_through_service():
    bad = []
    for module, path, name in cross_module_imports():
        parts = name.split(".")
        target = parts[2]
        # permitido: "from app.modules.X import service" e "from app.modules.X.service import ..."
        if name in (f"app.modules.{target}", f"app.modules.{target}.service"):
            continue
        if len(parts) >= 4 and parts[3] == "service":
            continue
        bad.append(f"{module}/{path.name} importa {name}")
    assert not bad, "\n".join(bad)


def test_dependencies_follow_the_graph():
    bad = sorted({f"{module} → {name.split('.')[2]} ({path.name})"
                  for module, path, name in cross_module_imports()
                  if name.split(".")[2] not in ALLOWED[module]})
    assert not bad, "dependências fora do grafo:\n" + "\n".join(bad)


def test_graph_has_no_cycles():
    seen, stack = set(), set()

    def visit(node):
        assert node not in stack, f"ciclo envolvendo {node}"
        if node in seen:
            return
        stack.add(node)
        for dep in ALLOWED[node]:
            visit(dep)
        stack.discard(node)
        seen.add(node)

    for module in MODULES:
        visit(module)


@pytest.mark.parametrize("module", MODULES)
def test_service_does_not_import_web_framework(module):
    path = MODULES_DIR / module / "service.py"
    bad = [n for n in imports(path) if n.split(".")[0] in {"fastapi", "starlette"}]
    assert not bad, f"{module}/service.py importa {bad}"


def test_routers_do_not_raise_http_exception():
    bad = [f"{p.parent.name}/router.py" for _, p in module_files()
           if p.name == "router.py" and "HTTPException" in p.read_text()]
    assert not bad, bad


def test_models_have_no_relationship():
    bad = [f"{p.parent.name}/models.py" for _, p in module_files()
           if p.name == "models.py" and "Relationship" in p.read_text()]
    assert not bad, bad


def test_core_does_not_depend_on_modules():
    core = MODULES_DIR.parent / "core"
    for path in core.glob("*.py"):
        names = imports(path)
        allowed = {"app.modules", "app.modules.registry"} if path.name == "db.py" else set()
        bad = [n for n in names if n.startswith("app.modules") and n not in allowed]
        assert not bad, f"core/{path.name} importa {bad}"
