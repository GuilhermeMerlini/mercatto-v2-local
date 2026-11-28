import { FC, useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Product } from "../api/types";
import { Card } from "../components/ui/Card";
import { Price } from "../components/ui/Price";
import { StarRating } from "../components/ui/StarRating";
import { Spinner } from "../components/ui/Spinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { Button } from "../components/ui/Button";
import { Select } from "../components/ui/Select";
import { useAuth } from "../auth/AuthContext";
import { useCart } from "../cart/CartContext";
import "./Product.css";

/** Quantidade e "Add to cart". Fica em componente próprio, com key, para zerar ao trocar de produto. */
function BuyBox({ product }: { product: Product }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addItem } = useCart();
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inStock = product.stock > 0;
  const options = Array.from({ length: Math.min(10, product.stock) }, (_, i) => i + 1);

  const handleAddToCart = async () => {
    if (!user) {
      navigate(`/signin?next=/products/${product.id}`);
      return;
    }
    setAdding(true);
    setError(null);
    try {
      await addItem(product.id, quantity);
      setAdded(true);
    } catch (err) {
      setAdded(false);
      setError(err instanceof ApiError ? err.detail : "Could not add to cart");
    } finally {
      setAdding(false);
    }
  };

  return (
    <>
      {inStock && (
        <Select label="Quantity" value={quantity} onChange={(e) => setQuantity(Number(e.target.value))}>
          {options.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </Select>
      )}
      <Button variant="primary" onClick={handleAddToCart} disabled={!inStock} loading={adding}>
        Add to cart
      </Button>
      {added && (
        <div role="status" className="product-added-to-cart">
          Added to cart
          <Link to="/cart" className="product-added-to-cart__link">View cart</Link>
        </div>
      )}
      {error && <ErrorMessage>{error}</ErrorMessage>}
    </>
  );
}

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
        <div data-slot="buy-box">
          <BuyBox key={product.id} product={product} />
        </div>
      </Card>
    </div>
  );
};

export default Product;
