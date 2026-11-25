import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { ProductCard } from "../components/ProductCard";
import { Spinner } from "../components/ui/Spinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { Pagination } from "../components/ui/Pagination";
import { Select } from "../components/ui/Select";
import { Input } from "../components/ui/Input";
import { SearchResult } from "../api/types";
import "./Search.css";

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const page = parseInt(searchParams.get("page") || "1", 10);
  const q = searchParams.get("q") || "";
  const category = searchParams.get("category") || "";
  const minPrice = searchParams.get("min_price") || "";
  const maxPrice = searchParams.get("max_price") || "";
  const minRating = searchParams.get("min_rating") || "";
  const sort = searchParams.get("sort") || "relevance";

  const fetchSearch = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (q) params.append("q", q);
      if (category) params.append("category", category);
      if (minPrice) params.append("min_price_cents", Math.round(parseFloat(minPrice) * 100).toString());
      if (maxPrice) params.append("max_price_cents", Math.round(parseFloat(maxPrice) * 100).toString());
      if (minRating) params.append("min_rating", minRating);
      if (sort) params.append("sort", sort);
      params.append("page", page.toString());
      params.append("page_size", "20");

      const response = await api<SearchResult>(`/api/search/products?${params.toString()}`);
      setResults(response);
    } catch (err) {
      setError("Could not load the search results");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [q, category, minPrice, maxPrice, minRating, sort, page]);

  useEffect(() => {
    fetchSearch();
  }, [fetchSearch]);

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      newParams.set("sort", e.target.value);
      newParams.delete("page");
      return newParams;
    });
  };

  const handleMinRatingChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      if (e.target.value) {
        newParams.set("min_rating", e.target.value);
      } else {
        newParams.delete("min_rating");
      }
      newParams.delete("page");
      return newParams;
    });
  };

  const handleMinPriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      if (value) {
        newParams.set("min_price", value);
      } else {
        newParams.delete("min_price");
      }
      newParams.delete("page");
      return newParams;
    });
  };

  const handleMaxPriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      if (value) {
        newParams.set("max_price", value);
      } else {
        newParams.delete("max_price");
      }
      newParams.delete("page");
      return newParams;
    });
  };

  const handlePageChange = (newPage: number) => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      newParams.set("page", newPage.toString());
      return newParams;
    });
  };

  const title = q ? `Results for "${q}"` : category || "All products";
  const correctedQuery = results?.corrected_query;
  const total = results?.total || 0;

  return (
    <div className="search">
      <h1 className="search__title">{title}</h1>
      {correctedQuery && (
        <p className="search__corrected">Showing results for "{correctedQuery}"</p>
      )}
      <p className="search__total">{total} {total === 1 ? "product" : "products"}</p>
      <div className="search__filters">
        <Select
          label="Sort by"
          value={sort}
          onChange={handleSortChange}
        >
          <option value="relevance">Relevance</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
          <option value="rating">Top rated</option>
        </Select>
        <Input
          label="Min price"
          type="number"
          value={minPrice}
          onChange={handleMinPriceChange}
          min="0"
          step="0.01"
        />
        <Input
          label="Max price"
          type="number"
          value={maxPrice}
          onChange={handleMaxPriceChange}
          min="0"
          step="0.01"
        />
        <Select
          label="Minimum rating"
          value={minRating}
          onChange={handleMinRatingChange}
        >
          <option value="">Any</option>
          <option value="4">4+</option>
          <option value="3">3+</option>
          <option value="2">2+</option>
        </Select>
      </div>
      {loading ? (
        <Spinner />
      ) : error ? (
        <ErrorMessage>{error}</ErrorMessage>
      ) : results?.items.length === 0 ? (
        <EmptyState title="No products found" />
      ) : (
        <>
          <div className="search__products">
            {results?.items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          {results && (
            <Pagination
              page={page}
              total={total}
              pageSize={20}
              onChange={handlePageChange}
            />
          )}
        </>
      )}
    </div>
  );
}
