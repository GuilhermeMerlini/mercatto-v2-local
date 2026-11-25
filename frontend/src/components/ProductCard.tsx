import { Link } from "react-router-dom";
import type { Product } from "../api/types";
import { Price } from "./ui/Price";
import { StarRating } from "./ui/StarRating";
import "./ProductCard.css";

export function ProductCard({ product }: { product: Product }) {
  return (
    <article className="product-card">
      {product.image_url ? (
        <Link to={`/products/${product.id}`}>
          <img
            src={product.image_url}
            alt={product.name}
            loading="lazy"
            className="product-card__image"
          />
        </Link>
      ) : (
        <div className="product-card__placeholder" aria-hidden="true" />
      )}
      <Link to={`/products/${product.id}`} className="product-card__name">
        {product.name}
      </Link>
      <Price cents={product.price_cents} listCents={product.list_price_cents} />
      {product.review_count > 0 && (
        <div className="product-card__rating">
          <StarRating value={product.average_rating} count={product.review_count} />
        </div>
      )}
      {product.stock === 0 && (
        <div className="product-card__out-of-stock">Esgotado</div>
      )}
    </article>
  );
}
