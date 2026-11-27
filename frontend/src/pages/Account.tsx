import { useEffect, useState } from "react";

import { useAuth } from "../auth/AuthContext";
import { api, ApiError } from "../api/client";
import type { User } from "../api/types";
import { Button, Card, ErrorMessage, Input } from "../components/ui";
import "./Account.css";

const fallbackError = (err: unknown) =>
  err instanceof ApiError ? err.detail : "Something went wrong. Try again.";

function PersonalDetails({ user, onSaved }: { user: User; onSaved: () => Promise<void> }) {
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [emailError, setEmailError] = useState<string>();
  const [error, setError] = useState<string>();
  const [status, setStatus] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  // Mantém os campos em dia quando o usuário do contexto muda (ex.: depois do refreshUser).
  useEffect(() => {
    setName(user.name);
    setEmail(user.email);
  }, [user.name, user.email]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError(undefined);
    setError(undefined);
    setStatus(undefined);
    setSubmitting(true);
    try {
      await api<User>("/api/users/me", { method: "PATCH", body: { name, email } });
      await onSaved();
      setStatus("Details updated");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setEmailError("This email is already registered");
      } else {
        setError(fallbackError(err));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section aria-labelledby="account-details-title">
      <h2 id="account-details-title" className="account__section-title">
        Personal details
      </h2>
      <form className="account__form" onSubmit={handleSubmit} noValidate>
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
          error={emailError}
          required
        />
        {error && <ErrorMessage>{error}</ErrorMessage>}
        <div className="account__actions">
          <Button type="submit" variant="primary" loading={submitting}>
            Save
          </Button>
          <div role="status" className="account__status">
            {status}
          </div>
        </div>
      </form>
    </section>
  );
}

type PasswordErrors = { current?: string; next?: string; confirm?: string };

function ChangePassword() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<PasswordErrors>({});
  const [error, setError] = useState<string>();
  const [status, setStatus] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  const validate = () => {
    const found: PasswordErrors = {};
    if (newPassword.length < 8) {
      found.next = "Password must be at least 8 characters";
    }
    if (newPassword !== confirmPassword) {
      found.confirm = "Passwords do not match";
    }
    setFieldErrors(found);
    return Object.keys(found).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(undefined);
    setStatus(undefined);
    if (!validate()) return;

    setSubmitting(true);
    try {
      await api("/api/users/me/password", {
        method: "PUT",
        body: { current_password: currentPassword, new_password: newPassword },
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setStatus("Password changed");
    } catch (err) {
      // 400 é senha atual errada: fica no campo e não desloga (só 401 desloga).
      if (err instanceof ApiError && err.status === 400) {
        setFieldErrors({ current: err.detail });
      } else {
        setError(fallbackError(err));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section aria-labelledby="account-password-title">
      <h2 id="account-password-title" className="account__section-title">
        Change password
      </h2>
      <form className="account__form" onSubmit={handleSubmit} noValidate>
        <Input
          label="Current password"
          type="password"
          autoComplete="current-password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          error={fieldErrors.current}
          required
        />
        <Input
          label="New password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          hint="At least 8 characters"
          error={fieldErrors.next}
          required
        />
        <Input
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={fieldErrors.confirm}
          required
        />
        {error && <ErrorMessage>{error}</ErrorMessage>}
        <div className="account__actions">
          <Button type="submit" variant="primary" loading={submitting}>
            Change password
          </Button>
          <div role="status" className="account__status">
            {status}
          </div>
        </div>
      </form>
    </section>
  );
}

export default function Account() {
  const { user, refreshUser } = useAuth();

  // A rota é protegida pelo RequireAuth, então o user existe; a checagem é só para o TypeScript.
  if (!user) return null;

  return (
    <div className="account">
      <h1 className="account__title">My account</h1>
      <Card className="account__card">
        <PersonalDetails user={user} onSaved={refreshUser} />
      </Card>
      <Card className="account__card">
        <ChangePassword />
      </Card>
    </div>
  );
}
