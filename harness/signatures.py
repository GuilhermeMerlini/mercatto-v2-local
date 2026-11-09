"""Extrai só a API pública (assinaturas) de um arquivo, para injetar no prompt sem o corpo.

Python: imports, constantes MAIÚSCULAS, classes (campos, membros de enum, métodos sem corpo)
e funções públicas (assinatura + docstring). Nomes começando com "_" ficam de fora.
TypeScript: declarações `export` (tipos/interfaces inteiros; funções, componentes e
classes só até o início do corpo).
"""
import ast
import copy
import re

ELLIPSIS = ast.Expr(ast.Constant(...))


def _docstring_node(node):
    doc = ast.get_docstring(node, clean=False)
    return [ast.Expr(ast.Constant(doc))] if doc else []


def _stub_function(node):
    stub = copy.deepcopy(node)
    stub.body = _docstring_node(node) + [ELLIPSIS]
    return stub


def _stub_class(node):
    stub = copy.deepcopy(node)
    body = _docstring_node(node)
    for item in node.body:
        if isinstance(item, (ast.AnnAssign, ast.Assign)):
            body.append(item)  # campos de dataclass/model e membros de enum
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not item.name.startswith("_") or item.name == "__init__":
                body.append(_stub_function(item))
    stub.body = body or [ELLIPSIS]
    return stub


def _assigned_names(node):
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return [t.id for t in targets if isinstance(t, ast.Name)]


def python_signatures(source: str) -> str:
    tree = ast.parse(source)
    doc = ast.get_docstring(tree, clean=False)
    header = [f'"""{doc}"""'] if doc else []
    imports, out = [], []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            out.append(_stub_function(node))
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            out.append(_stub_class(node))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            if any(n.isupper() for n in _assigned_names(node)):
                out.append(node)
    parts = header + (["\n".join(imports)] if imports else []) + [ast.unparse(n) for n in out]
    return "\n\n".join(parts)


TS_BLOCK_DECL = re.compile(r"^export\s+(declare\s+)?(type|interface|enum)\b")


def typescript_signatures(source: str) -> str:
    lines = source.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("export"):
            i += 1
            continue
        if TS_BLOCK_DECL.match(line):
            # tipo/interface/enum: inclui inteiro (é API), contando chaves
            block, depth = [], 0
            while i < len(lines):
                block.append(lines[i])
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
                if depth <= 0 and (block[-1].rstrip().endswith((";", "}")) or "{" not in "".join(block)):
                    break
            out.append("\n".join(block))
            continue
        # função/componente/classe/const: só até o início do corpo
        header, parens = [], 0
        while i < len(lines):
            current = lines[i]
            header.append(current)
            parens += current.count("(") - current.count(")")
            i += 1
            stripped = current.rstrip()
            if parens <= 0 and (stripped.endswith(("{", "=>", ";")) or "=> {" in stripped):
                break
        text = "\n".join(header).rstrip()
        if text.endswith(";"):
            out.append(text)
        else:
            out.append(re.sub(r"\{\s*$", "", text).rstrip() + " { ... }")
    return "\n\n".join(out)


def signatures(path: str, source: str) -> str:
    if path.endswith(".py"):
        return python_signatures(source)
    if path.endswith((".ts", ".tsx")):
        return typescript_signatures(source)
    return source
