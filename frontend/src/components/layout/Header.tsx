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
          label="Buscar produtos"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="header__search-input"
        />
        <Button type="submit" variant="primary">Buscar</Button>
      </form>

      <div className="header__user">
        {user ? (
          <>
            <span className="header__user-name">{user.name}</span>
            <Link to="/orders" className="header__link">Meus pedidos</Link>
            <Link to="/account" className="header__link">Minha conta</Link>
            {user.role === "SELLER" && <Link to="/seller" className="header__link">Painel do vendedor</Link>}
            <Button variant="ghost" onClick={logout}>Sair</Button>
          </>
        ) : (
          <Link to="/signin" className="header__link">Entrar</Link>
        )}
      </div>
    </header>
  );
}
