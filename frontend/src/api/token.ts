export function getToken(): string | null {
  try {
    return localStorage.getItem("mercatto.token");
  } catch {
    return null;
  }
}

export function setToken(t: string): void {
  try {
    localStorage.setItem("mercatto.token", t);
  } catch {}
}

export function clearToken(): void {
  try {
    localStorage.removeItem("mercatto.token");
  } catch {}
}
