import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { api, ApiError, onUnauthorized } from "../api/client";
import { getToken, setToken, clearToken } from "../api/token";
import { User, LoginResponse } from "../api/types";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { name: string; email: string; password: string; role: "BUYER" | "SELLER" }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  useEffect(() => onUnauthorized(logout), [logout]);

  const loadUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const userData = await api<User>("/api/users/me");
      setUser(userData);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearToken();
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email: string, password: string) => {
    const response = await api<LoginResponse>("/api/users/login", {
      method: "POST",
      body: { email, password },
    });
    setToken(response.access_token);
    setUser(response);
  };

  const register = async (data: { name: string; email: string; password: string; role: "BUYER" | "SELLER" }) => {
    await api<User>("/api/users/register", {
      method: "POST",
      body: data,
    });
    await login(data.email, data.password);
  };


  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
