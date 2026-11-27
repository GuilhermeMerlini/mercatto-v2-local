import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Button, Card, ErrorMessage, Input } from "../components/ui";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";
import "./SignIn.css";

export default function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const nextParam = new URLSearchParams(location.search).get("next");
  const next = nextParam || "/";

  // Quem já está logado não precisa desta página. Durante o envio quem navega é o handleSubmit.
  useEffect(() => {
    if (!loading && user && !submitting) {
      navigate("/", { replace: true });
    }
  }, [user, loading, submitting, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await login(email, password);
      navigate(next);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Incorrect email or password");
      } else {
        setError(err instanceof ApiError ? err.detail : "Something went wrong. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const registerHref = nextParam ? `/register?next=${encodeURIComponent(nextParam)}` : "/register";

  return (
    <div className="sign-in">
      <Card className="sign-in__card">
        <h1 className="sign-in__title">Sign in</h1>
        <form className="sign-in__form" noValidate onSubmit={handleSubmit}>
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <ErrorMessage>{error}</ErrorMessage>}
          <Button type="submit" variant="primary" loading={submitting}>
            Sign in
          </Button>
        </form>
        <p className="sign-in__footer">
          New to Mercatto? <Link to={registerHref}>Create account</Link>
        </p>
      </Card>
    </div>
  );
}
