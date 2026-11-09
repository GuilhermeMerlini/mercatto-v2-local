import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.modules.search import ranker

RANKER = Path(__file__).resolve().parent.parent / "app" / "modules" / "search" / "ranker.py"


def product(id, name, brand=None, category="Geral", description=None):
    return SimpleNamespace(id=id, name=name, brand=brand, category=category, description=description)


# ---------- normalização ----------


def test_normalize_lowercases_and_strips_accents():
    assert ranker.normalize("Eletrônicos e Ação") == "eletronicos e acao"
    assert ranker.normalize(None) == ""


def test_tokenize():
    assert ranker.tokenize("Fone Bluetooth, 2ª geração (Preto)") == ["fone", "bluetooth", "2a", "geracao", "preto"]
    assert ranker.tokenize(None) == []
    assert ranker.tokenize("  --  ") == []


def test_query_terms_drop_stop_words():
    assert ranker.query_terms("The case for an iPhone") == ["case", "iphone"]
    assert ranker.query_terms("capa para celular") == ["capa", "celular"]
    assert ranker.query_terms("the of") == []


@pytest.mark.parametrize(
    "token, expected",
    [("batteries", "battery"), ("boxes", "box"), ("laptops", "laptop"), ("bus", "bus"),
     ("tie", "tie"), ("cats", "cat"), ("glass", "glas")],
)
def test_stem(token, expected):
    assert ranker.stem(token) == expected


@pytest.mark.parametrize(
    "term, token, expected",
    [
        ("laptop", "laptop", True),
        ("laptops", "laptop", True),  # mesmo radical
        ("lap", "laptop", True),  # prefixo com 3+ letras
        ("la", "laptop", False),  # prefixo curto demais
        ("top", "laptop", False),  # só prefixo, não substring
        ("battery", "batteries", True),
        ("mouse", "mice", False),
    ],
)
def test_term_matches(term, token, expected):
    assert ranker.term_matches(term, token) is expected


def test_name_head_tokens():
    assert ranker.name_head_tokens("Capa Slim for iPhone 15") == ["capa", "slim"]
    assert ranker.name_head_tokens("Cabo USB compatible with Samsung") == ["cabo", "usb"]
    assert ranker.name_head_tokens("For Dummies Guide") == ["for", "dummies", "guide"]
    assert ranker.name_head_tokens("Mesa de jantar") == ["mesa", "de", "jantar"]


# ---------- score e rank ----------


def test_every_term_must_match_somewhere():
    p = product(1, "Mouse sem fio", brand="Logi", category="Periféricos", description="Silencioso")
    assert ranker.score_product(p, ["mouse", "silencioso"]) is not None
    assert ranker.score_product(p, ["mouse", "teclado"]) is None


def test_matching_ignores_accents_and_case():
    p = product(1, "Câmera Fotográfica")
    assert ranker.score_product(p, ranker.query_terms("CAMERA fotografica")) is not None


def test_tiers_order_results():
    head = product(1, "Desk Lamp")
    brand = product(2, "Pen Holder", brand="Desko")
    in_name = product(3, "Laptop Stand for Desk")
    category = product(4, "Organizer", category="Desk Accessories")
    description = product(5, "Cushion", description="great for any desk")
    unrelated = product(6, "Garden Hose")
    pool = [description, unrelated, category, in_name, brand, head]
    assert [p.id for p in ranker.rank(pool, ["desk"])] == [1, 2, 3, 4, 5]


def test_tier_scores():
    assert ranker.score_product(product(1, "Desk Lamp"), ["desk"]) >= 4
    assert 3 <= ranker.score_product(product(2, "Pen", brand="Desko"), ["desk"]) < 4
    assert 2 <= ranker.score_product(product(3, "Stand for Desk"), ["desk"]) < 3
    assert 1 <= ranker.score_product(product(4, "Box", category="Desk"), ["desk"]) < 2
    assert 0 <= ranker.score_product(product(5, "Box", description="desk"), ["desk"]) < 1


def test_contiguous_phrase_wins_inside_same_tier():
    scattered = product(1, "Cable Braided USB")
    phrase = product(2, "USB Cable 2m")
    assert [p.id for p in ranker.rank([scattered, phrase], ["usb", "cable"])] == [2, 1]


def test_ties_are_broken_by_id():
    pool = [product(3, "Caneca Azul"), product(1, "Caneca Verde"), product(2, "Caneca Rosa")]
    assert [p.id for p in ranker.rank(pool, ["caneca"])] == [1, 2, 3]


def test_rank_without_matches_is_empty():
    assert ranker.rank([product(1, "Caneca")], ["notebook"]) == []


# ---------- typos ----------


@pytest.mark.parametrize(
    "a, b, d",
    [("", "", 0), ("abc", "", 3), ("kitten", "sitting", 3), ("laptop", "laptpo", 2), ("same", "same", 0)],
)
def test_edit_distance(a, b, d):
    assert ranker.edit_distance(a, b) == d


def test_vocabulary_uses_name_brand_and_category_only():
    vocab = ranker.vocabulary([product(1, "Mouse Gamer", brand="Logi", category="Periféricos",
                                       description="ergonomico")])
    assert vocab == {"mouse", "gamer", "logi", "perifericos"}


VOCAB = {"laptop", "mouse", "keyboard", "headphones"}


@pytest.mark.parametrize(
    "terms, expected",
    [
        (["laptoq"], ["laptop"]),  # 1 edição
        (["keybaord"], ["keyboard"]),  # 8+ letras: até 2 edições
        (["laptpo", "mouse"], None),  # 6 letras com 2 edições: não corrige
        (["mous"], None),  # prefixo de palavra do vocabulário: não é typo
        (["xyzw"], None),  # nada próximo
        (["abc"], None),  # menos de 4 letras: não corrige
        (["mouze", "laptoq"], ["mouse", "laptop"]),
    ],
)
def test_correct_terms(terms, expected):
    assert ranker.correct_terms(terms, VOCAB) == expected


def test_correct_terms_tie_picks_alphabetical():
    assert ranker.correct_terms(["carx"], {"cart", "card"}) == ["card"]


def test_ranker_is_pure():
    tree = ast.parse(RANKER.read_text())
    imported = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imported += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    banned = ("fastapi", "starlette", "sqlmodel", "sqlalchemy", "app.modules", "app.core.db")
    assert not [m for m in imported if m.startswith(banned)]
