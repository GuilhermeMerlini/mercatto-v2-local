import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api/client";
import type { Cart } from "../api/types";

interface CartContextType {
  cart: Cart | null;
  loading: boolean;
  addItem: (productId: number, quantity: number) => Promise<void>;
  updateQuantity: (productId: number, quantity: number) => Promise<void>;
  removeItem: (productId: number) => Promise<void>;
  saveForLater: (productId: number) => Promise<void>;
  moveToCart: (productId: number) => Promise<void>;
  clear: () => Promise<void>;
  refresh: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!user) {
      setCart(null);
      setLoading(false);
      return;
    }

    try {
      const cartData = await api<Cart>(`/api/cart/${user.id}`);
      setCart(cartData);
    } catch {
      setCart(null);
    } finally {
      setLoading(false);
    }
  }, [user]);

  const addItem = useCallback(async (productId: number, quantity: number) => {
    if (!user) return;
    const cartData = await api<Cart>(`/api/cart/${user.id}/items`, {
      method: "POST",
      body: { product_id: productId, quantity },
    });
    setCart(cartData);
  }, [user]);

  const updateQuantity = useCallback(async (productId: number, quantity: number) => {
    if (!user) return;
    const cartData = await api<Cart>(`/api/cart/${user.id}/items/${productId}`, {
      method: "PUT",
      body: { quantity },
    });
    setCart(cartData);
  }, [user]);

  const removeItem = useCallback(async (productId: number) => {
    if (!user) return;
    const cartData = await api<Cart>(`/api/cart/${user.id}/items/${productId}`, {
      method: "DELETE",
    });
    setCart(cartData);
  }, [user]);

  const saveForLater = useCallback(async (productId: number) => {
    if (!user) return;
    const cartData = await api<Cart>(`/api/cart/${user.id}/items/${productId}/save-for-later`, {
      method: "POST",
    });
    setCart(cartData);
  }, [user]);

  const moveToCart = useCallback(async (productId: number) => {
    if (!user) return;
    const cartData = await api<Cart>(`/api/cart/${user.id}/items/${productId}/move-to-cart`, {
      method: "POST",
    });
    setCart(cartData);
  }, [user]);

  const clear = useCallback(async () => {
    if (!user) return;
    const cartData = await api<Cart>(`/api/cart/${user.id}`, {
      method: "DELETE",
    });
    setCart(cartData);
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <CartContext.Provider value={{ cart, loading, addItem, updateQuantity, removeItem, saveForLater, moveToCart, clear, refresh }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
