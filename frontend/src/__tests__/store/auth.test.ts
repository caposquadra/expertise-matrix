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

  it("logout clears user", async () => {
    useAuth.getState().setUser(mockUser);

    await useAuth.getState().logout();

    const { user } = useAuth.getState();
    expect(user).toBeNull();
  });
});
