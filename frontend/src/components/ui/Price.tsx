import { formatCents } from "../../lib/money";
import "./Price.css";

interface PriceProps {
  cents: number;
  listCents?: number | null;
}

export function Price({ cents, listCents }: PriceProps) {
  const formattedPrice = formatCents(cents);

  if (listCents && listCents > cents) {
    const discount = Math.round(100 * (1 - cents / listCents));
    const formattedListPrice = formatCents(listCents);

    return (
      <span className="price">
        <span className="price__current">{formattedPrice}</span>
        <s className="price__old">{formattedListPrice}</s>
        <span className="price__badge">-{discount}%</span>
      </span>
    );
  }

  return (
    <span className="price">
      <span className="price__current">{formattedPrice}</span>
    </span>
  );
}
