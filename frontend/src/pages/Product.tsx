import { FC, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Product } from "../api/types";
import { Card } from "../components/ui/Card";
import { Price } from "../components/ui/Price";
import { StarRating } from "../components/ui/StarRating";
import { Spinner } from "../components/ui/Spinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import "./Product.css";

const Product: FC = () => {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    const fetchProduct = async () => {
      setLoading(true);
      setNotFound(false);
      setError(null);
      try {
        const data = await api<Product>(`/api/catalog/products/${id}`);
        if (!cancelled) setProduct(data);
      } catch (err) {
        if (cancelled) return;
        setProduct(null);
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true);
        } else {
          setError("Could not load the product");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchProduct();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="product-page">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="product-page">
        <ErrorMessage>{error}</ErrorMessage>
      </div>
    );
  }

  if (notFound || !product) {
    return (
      <div className="product-page">
        <EmptyState title="Product not found" />
      </div>
    );
  }

  const { image_url, name, brand, average_rating, review_count, price_cents, list_price_cents, description, model_number, warranty_months, stock } = product;

  const inStock = stock > 0;
  const lowStock = inStock && stock < 10;
  const hasWarranty = warranty_months !== null && warranty_months !== undefined;
  const hasDetails = Boolean(model_number) || hasWarranty;

  return (
    <div className="product-page">
      <Card as="article" className="product-page__card">
        {image_url && <img src={image_url} alt={name} className="product-image" />}
        <h1 className="product-name">{name}</h1>
        {brand && <div className="product-brand">{brand}</div>}
        {review_count > 0 && <StarRating value={average_rating} count={review_count} />}
        <Price cents={price_cents} listCents={list_price_cents} />
        {description && <p className="product-description">{description}</p>}
        {hasDetails && (
          <dl className="product-details">
            {model_number && (
              <>
                <dt className="product-detail-label">Model</dt>
                <dd className="product-detail-value">{model_number}</dd>
              </>
            )}
            {hasWarranty && (
              <>
                <dt className="product-detail-label">Warranty</dt>
                <dd className="product-detail-value">{warranty_months} months</dd>
              </>
            )}
          </dl>
        )}
        <div className="product-availability">
          {stock === 0 ? (
            <span className="product-out-of-stock">Out of stock</span>
          ) : (
            <>
              <span className="product-in-stock">In stock</span>
              {lowStock && <span className="product-low-stock">Only {stock} left</span>}
            </>
          )}
        </div>
        <div data-slot="buy-box" />
      </Card>
    </div>
  );
};

export default Product;
