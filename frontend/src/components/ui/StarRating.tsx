import "./StarRating.css";

interface StarRatingProps {
  value: number;
  count?: number;
}

export function StarRating({ value, count }: StarRatingProps) {
  const stringValue = value.toFixed(1).replace('.', ',');
  const ariaLabel = `Nota ${stringValue} de 5`;
  // Arredonda para a meia estrela mais próxima; a camada cheia é cortada nessa largura.
  const filled = Math.min(5, Math.max(0, Math.round(value * 2) / 2));

  return (
    <span className="star-rating">
      <span role="img" aria-label={ariaLabel} className="star-rating__stars">
        <span className="star-rating__empty">☆☆☆☆☆</span>
        <span className="star-rating__full" style={{ width: `${(filled / 5) * 100}%` }}>
          ★★★★★
        </span>
      </span>
      {count !== undefined && <span className="star-rating__count">({count})</span>}
    </span>
  );
}
