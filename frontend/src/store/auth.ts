import { create } from "zustand";
import client from "../api/client";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  grade: string | null;
  team_id: string | null;
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  setUser: (user: User) => void;
  logout: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  logout: async () => {
    try {
      await client.post("/auth/logout");
    } catch {
      // ignore — tokens will be cleared anyway
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null });
  },
}));
