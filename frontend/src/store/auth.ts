import { create } from "zustand";
import client, { setAccessToken } from "../api/client";

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
  initialized: boolean;
  setUser: (user: User) => void;
  logout: () => Promise<void>;
  restoreSession: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  initialized: false,
  setUser: (user) => set({ user }),
  logout: async () => {
    try {
      await client.post("/auth/logout");
    } catch {
      // ignore — server will clear cookie
    }
    setAccessToken(null);
    set({ user: null });
  },
  restoreSession: async () => {
    try {
      const { data } = await client.post("/auth/refresh", {});
      setAccessToken(data.access_token);
      const me = await client.get("/auth/me");
      set({ user: me.data, initialized: true });
    } catch {
      set({ initialized: true });
    }
  },
}));
