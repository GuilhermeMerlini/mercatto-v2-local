from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.core.errors import InvalidInputError
from app.modules.catalog.service import filter_products, ProductView
from app.modules.search.ranker import query_terms, correct_terms, vocabulary, rank


@dataclass(frozen=True)
class SearchResult:
    items: list[ProductView]
    total: int
    page: int
    page_size: int
    corrected_query: Optional[str]


def search_products(
    session: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price_cents: Optional[int] = None,
    max_price_cents: Optional[int] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> SearchResult:
    # Validação de entrada
    if page < 1:
        raise InvalidInputError("Page must be >= 1")
    if page_size < 1:
        raise InvalidInputError("Page size must be >= 1")
    if min_price_cents is not None and min_price_cents < 0:
        raise InvalidInputError("Min price cannot be negative")
    if max_price_cents is not None and max_price_cents < 0:
        raise InvalidInputError("Max price cannot be negative")
    if min_price_cents is not None and max_price_cents is not None and min_price_cents > max_price_cents:
        raise InvalidInputError("Min price cannot be greater than max price")
    if min_rating is not None and (min_rating < 0 or min_rating > 5):
        raise InvalidInputError("Min rating must be between 0 and 5")
    
    sort = sort.lower() if sort else "relevance"
    valid_sorts = {"relevance", "price_asc", "price_desc", "rating"}
    if sort not in valid_sorts:
        raise InvalidInputError(f"Sort must be one of {valid_sorts}")

    # Filtragem de produtos
    candidates = filter_products(
        session,
        category=category,
        min_price_cents=min_price_cents,
        max_price_cents=max_price_cents,
        min_rating=min_rating
    )

    # Processamento de texto
    corrected_query = None
    ranked_items = candidates

    if query:
        terms = query_terms(query)
        if terms:
            ranked_items = rank(candidates, terms)
            if not ranked_items:
                vocab = vocabulary(candidates)
                corrected = correct_terms(terms, vocab)
                if corrected:
                    retry = rank(candidates, corrected)
                    if retry:
                        corrected_query = " ".join(corrected)
                        ranked_items = retry
        else:
            # Sem termos, ordenar por id
            ranked_items = sorted(candidates, key=lambda p: p.id)

    # Ordenação
    if sort == "price_asc":
        ranked_items.sort(key=lambda p: (p.price_cents, p.id))
    elif sort == "price_desc":
        ranked_items.sort(key=lambda p: (-p.price_cents, p.id))
    elif sort == "rating":
        ranked_items.sort(key=lambda p: (-p.average_rating, -p.review_count, p.id))

    # Paginação
    total = len(ranked_items)
    start = (page - 1) * page_size
    end = start + page_size
    items = ranked_items[start:end]

    return SearchResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        corrected_query=corrected_query
    )
