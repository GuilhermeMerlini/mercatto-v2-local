import re
import unicodedata
from typing import List, Optional, Set


def normalize(text: str) -> str:
    if text is None:
        return ""
    # Normaliza para NFKD e remove combinantes
    normalized = unicodedata.normalize('NFKD', text)
    without_accents = ''.join(c for c in normalized if not unicodedata.combining(c))
    return without_accents.lower()


def tokenize(text: str) -> List[str]:
    normalized = normalize(text)
    # Divide por não-letras/números e filtra vazios
    tokens = re.split(r'[^a-z0-9]+', normalized)
    return [t for t in tokens if t]


def query_terms(query: str) -> List[str]:
    stop_words = {
        'a', 'an', 'the', 'of', 'for', 'and', 'or', 'with',
        'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'para', 'com', 'um', 'uma',
    }
    tokens = tokenize(query)
    return [t for t in tokens if t not in stop_words]


def stem(token: str) -> str:
    if len(token) <= 3:
        return token
    if token.endswith('ies') and len(token) > 4:
        return token[:-3] + 'y'
    if token.endswith('es') and len(token) > 4:
        return token[:-2]
    if token.endswith('s') and len(token) > 3:
        return token[:-1]
    return token


def term_matches(term: str, token: str) -> bool:
    if term == token:
        return True
    if stem(term) == stem(token):
        return True
    if len(term) >= 3:
        return token.startswith(term) or stem(token).startswith(stem(term))
    return False


def name_head_tokens(name: str) -> List[str]:
    tokens = tokenize(name)
    if not tokens:
        return []
    head = [tokens[0]]
    tail_markers = {'for', 'compatible', 'with', 'fits', 'para', 'compativel'}
    for token in tokens[1:]:
        if token in tail_markers:
            break
        head.append(token)
    return head


def score_product(product, terms) -> Optional[float]:
    name_tokens = tokenize(product.name)
    brand_tokens = tokenize(product.brand) if product.brand else []
    category_tokens = tokenize(product.category) if product.category else []
    description_tokens = tokenize(product.description) if product.description else []

    all_tokens = name_tokens + brand_tokens + category_tokens + description_tokens

    # Verifica se todos os termos casam com algum token
    for term in terms:
        matched = False
        for token in all_tokens:
            if term_matches(term, token):
                matched = True
                break
        if not matched:
            return None

    # Calcula camada
    head_tokens = name_head_tokens(product.name)
    tier_score = 0.0

    # Verifica se todos os termos estão no início do nome
    if all(any(term_matches(t, ht) for ht in head_tokens) for t in terms):
        tier_score = 4.0
    elif any(any(term_matches(t, bt) for bt in brand_tokens) for t in terms):
        tier_score = 3.0
    elif all(any(term_matches(t, nt) for nt in name_tokens) for t in terms):
        tier_score = 2.0
    elif any(any(term_matches(t, ct) for ct in category_tokens) for t in terms):
        tier_score = 1.0
    else:
        tier_score = 0.0

    # Bônus de frase
    phrase_bonus = 0.0
    if len(terms) > 1:
        joined_terms = " ".join(terms)
        joined_name_tokens = " ".join(name_tokens)
        if joined_terms in joined_name_tokens:
            phrase_bonus = 0.5

    # Fração dos termos que casam no nome
    name_matches = sum(1 for t in terms if any(term_matches(t, nt) for nt in name_tokens))
    fraction = name_matches / len(terms) if terms else 0.0

    return tier_score + phrase_bonus + 0.4 * fraction


def rank(products, terms) -> List:
    scored = [(p, score_product(p, terms)) for p in products]
    valid = [(p, s) for p, s in scored if s is not None]
    # Ordena por score decrescente e id crescente em caso de empate
    valid.sort(key=lambda x: (-x[1], x[0].id))
    return [p for p, _ in valid]


def edit_distance(a: str, b: str) -> int:
    # Programação dinâmica para evitar exponencialidade
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[m][n]


def vocabulary(products) -> Set[str]:
    vocab = set()
    for p in products:
        vocab.update(tokenize(p.name))
        vocab.update(tokenize(p.brand) if p.brand else [])
        vocab.update(tokenize(p.category) if p.category else [])
    return vocab


def correct_terms(terms, vocab) -> Optional[List[str]]:
    corrected = []
    changed = False
    for term in terms:
        if len(term) < 4:
            corrected.append(term)
            continue
        if any(term_matches(term, v) for v in vocab):
            corrected.append(term)
            continue
        candidates = []
        for word in vocab:
            distance = edit_distance(term, word)
            max_dist = 2 if len(term) >= 8 else 1
            if distance <= max_dist:
                candidates.append((distance, word))
        if not candidates:
            corrected.append(term)
            continue
        candidates.sort(key=lambda x: (x[0], x[1]))
        corrected.append(candidates[0][1])
        changed = True
    return corrected if changed else None
