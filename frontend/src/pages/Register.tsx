import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Button, Card, ErrorMessage, Input } from "../components/ui";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";
import "./Register.css";

type Role = "BUYER" | "SELLER";
type Errors = { email?: string; password?: string; confirmPassword?: string; general?: string };

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<Role>("BUYER");
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const nextParam = new URLSearchParams(location.search).get("next");
  const next = nextParam || "/";

  const validate = () => {
    const found: Errors = {};
    if (password.length < 8) {
      found.password = "Password must be at least 8 characters";
    }
    if (password !== confirmPassword) {
      found.confirmPassword = "Passwords do not match";
    }
    setErrors(found);
    return Object.keys(found).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      // O register do contexto também faz o login.
      await register({ name, email, password, role });
      navigate(next);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setErrors({ email: "This email is already registered" });
      } else {
        setErrors({ general: err instanceof ApiError ? err.detail : "Something went wrong. Try again." });
      }
    } finally {
      setSubmitting(false);
    }
  };

  const signInHref = nextParam ? `/signin?next=${encodeURIComponent(nextParam)}` : "/signin";

  return (
    <div className="register">
      <Card className="register__card">
        <h1 className="register__title">Create account</h1>
        <form className="register__form" noValidate onSubmit={handleSubmit}>
          <Input
            label="Name"
            autoComplete="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            required
          />
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hint="At least 8 characters"
            error={errors.password}
            required
          />
          <Input
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
            required
          />
          <fieldset className="register__roles">
            <legend className="register__roles-legend">Account type</legend>
            <label className="register__role">
              <input
                type="radio"
                name="role"
                value="BUYER"
                checked={role === "BUYER"}
                onChange={() => setRole("BUYER")}
              />
              I want to buy
            </label>
            <label className="register__role">
              <input
                type="radio"
                name="role"
                value="SELLER"
                checked={role === "SELLER"}
                onChange={() => setRole("SELLER")}
              />
              I want to sell
            </label>
          </fieldset>
          {errors.general && <ErrorMessage>{errors.general}</ErrorMessage>}
          <Button type="submit" variant="primary" loading={submitting}>
            Create account
          </Button>
        </form>
        <p className="register__footer">
          Already have an account? <Link to={signInHref}>Sign in</Link>
        </p>
      </Card>
    </div>
  );
}
