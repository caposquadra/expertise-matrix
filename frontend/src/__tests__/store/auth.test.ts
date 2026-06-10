import { describe, it, expect, beforeEach } from "vitest";
import { useAuth } from "../../store/auth";

const mockUser = {
  id: "1",
  email: "test@test.com",
  full_name: "Test User",
  role: "employee",
  grade: "middle" as string | null,
  team_id: null,
  is_active: true,
};

describe("useAuth store", () => {
  beforeEach(() => {
    useAuth.setState({ user: null });
    localStorage.clear();
  });

  it("starts with null user", () => {
    const { user } = useAuth.getState();
    expect(user).toBeNull();
  });

  it("setUser updates user", () => {
    useAuth.getState().setUser(mockUser);
    const { user } = useAuth.getState();
    expect(user).toEqual(mockUser);
  });

  it("logout clears user and tokens", async () => {
    localStorage.setItem("access_token", "abc");
    localStorage.setItem("refresh_token", "xyz");
    useAuth.getState().setUser(mockUser);

    await useAuth.getState().logout();

    const { user } = useAuth.getState();
    expect(user).toBeNull();
    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
  });
});
