import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import type { Cart as CartData } from "../api/types";
import { useCart } from "../cart/CartContext";
import { Button, EmptyState, ErrorMessage, Price, Select, Spinner } from "../components/ui";
import "./Cart.css";

type CartItem = NonNullable<CartData["items"]>[number];

interface CartLineProps {
  item: CartItem;
  saved: boolean;
  busy: boolean;
  run: (action: () => Promise<void>) => void;
}

/** Uma linha do carrinho ou da lista "Saved for later". */
function CartLine({ item, saved, busy, run }: CartLineProps) {
  const { updateQuantity, removeItem, saveForLater, moveToCart } = useCart();
  // 1 a 10, ou até a quantidade atual se ela já passou de 10.
  const options = Array.from({ length: Math.max(10, item.quantity) }, (_, i) => i + 1);

  return (
    <li className="cart-item">
      {item.image_url && <img src={item.image_url} alt={item.product_name} className="cart-item__image" />}
      <div className="cart-item__info">
        <Link to={`/products/${item.product_id}`} className="cart-item__name">
          {item.product_name}
        </Link>
        <Price cents={item.unit_price_cents} />
        {!saved && (
          <Select
            label={`Quantity for ${item.product_name}`}
            value={item.quantity}
            disabled={busy}
            onChange={(e) => run(() => updateQuantity(item.product_id, Number(e.target.value)))}
          >
            {options.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </Select>
        )}
      </div>
      <div className="cart-item__actions">
        {saved ? (
          <Button variant="ghost" disabled={busy} onClick={() => run(() => moveToCart(item.product_id))}>
            Move to cart
          </Button>
        ) : (
          <Button variant="ghost" disabled={busy} onClick={() => run(() => saveForLater(item.product_id))}>
            Save for later
          </Button>
        )}
        <Button variant="ghost" disabled={busy} onClick={() => run(() => removeItem(item.product_id))}>
          Remove
        </Button>
      </div>
    </li>
  );
}

export default function Cart() {
  const { cart, loading } = useCart();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (loading || !cart) {
    return (
      <div className="cart-page">
        <Spinner />
      </div>
    );
  }

  /** Roda uma operação do carrinho, travando os botões e mostrando o erro, se houver. */
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update the cart");
    } finally {
      setBusy(false);
    }
  };

  const items = cart.items ?? [];
  const saved = cart.saved_for_later ?? [];
  const count = cart.item_count;

  return (
    <div className="cart-page">
      <h1>Cart</h1>
      {error && <ErrorMessage>{error}</ErrorMessage>}

      {items.length > 0 ? (
        <ul className="cart-items">
          {items.map((item) => (
            <CartLine key={item.product_id} item={item} saved={false} busy={busy} run={run} />
          ))}
        </ul>
      ) : (
        <EmptyState title="Your cart is empty">
          <Link to="/" className="cart-page__continue">
            Continue shopping
          </Link>
        </EmptyState>
      )}

      <div className="cart-summary">
        <p className="cart-summary__subtotal">
          Subtotal ({count} {count === 1 ? "item" : "items"})
        </p>
        <Price cents={cart.total_cents} />
        <Button variant="primary" disabled={items.length === 0} onClick={() => navigate("/checkout")}>
          Proceed to checkout
        </Button>
      </div>

      {saved.length > 0 && (
        <section aria-labelledby="cart-saved-title" className="cart-saved">
          <h2 id="cart-saved-title" className="cart-saved__title">
            Saved for later
          </h2>
          <ul className="cart-items">
            {saved.map((item) => (
              <CartLine key={item.product_id} item={item} saved busy={busy} run={run} />
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
