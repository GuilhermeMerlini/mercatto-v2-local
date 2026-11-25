import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import "./Header.css";

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <header className="header">
      <div className="header__brand">
        <Link to="/" className="header__logo">Mercatto</Link>
      </div>

      <form className="header__search" role="search" onSubmit={handleSubmit}>
        <Input
          label="Search products"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="header__search-input"
        />
        <Button type="submit" variant="primary">Search</Button>
      </form>

      <div className="header__user">
        {user ? (
          <>
            <span className="header__user-name">{user.name}</span>
            <Link to="/orders" className="header__link">My orders</Link>
            <Link to="/account" className="header__link">My account</Link>
            {user.role === "SELLER" && <Link to="/seller" className="header__link">Seller dashboard</Link>}
            <Button variant="ghost" onClick={logout}>Sign out</Button>
          </>
        ) : (
          <Link to="/signin" className="header__link">Sign in</Link>
        )}
      </div>
    </header>
  );
}
