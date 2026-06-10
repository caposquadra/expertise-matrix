import { describe, it, expect } from "vitest";
import { translateRole, translateGrade } from "../../constants";

describe("translateRole", () => {
  it("returns label for known role", () => {
    expect(translateRole("admin")).toBe("Администратор");
    expect(translateRole("manager")).toBe("Руководитель");
    expect(translateRole("employee")).toBe("Сотрудник");
    expect(translateRole("expert")).toBe("Эксперт");
  });

  it("returns fallback for unknown role", () => {
    expect(translateRole("unknown")).toBe("unknown");
  });

  it("returns em dash for null/undefined", () => {
    expect(translateRole(null)).toBe("—");
    expect(translateRole(undefined)).toBe("—");
  });
});

describe("translateGrade", () => {
  it("returns label for known grade", () => {
    expect(translateGrade("junior")).toBe("Младший тестировщик");
    expect(translateGrade("middle")).toBe("Тестировщик");
    expect(translateGrade("senior")).toBe("Старший тестировщик");
  });

  it("returns fallback for unknown grade", () => {
    expect(translateGrade("lead")).toBe("lead");
  });

  it("returns em dash for null/undefined", () => {
    expect(translateGrade(null)).toBe("—");
    expect(translateGrade(undefined)).toBe("—");
  });
});
