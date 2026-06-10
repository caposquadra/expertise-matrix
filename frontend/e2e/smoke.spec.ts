import { test, expect } from "@playwright/test";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";

const ADMIN = { email: "admin@example.com", password: "admin123" };
const MANAGER = { email: "manager@example.com", password: "manager123" };
const EMPLOYEE = { email: "ivan@example.com", password: "ivan123" };

test.describe("Authentication", () => {
  test("login as admin and see dashboard", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.loginAndExpect(ADMIN.email, ADMIN.password, /\//);
    await expect(page).toHaveURL(/\/$/);
  });

  test("login as employee and redirect to profile", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.loginAndExpect(EMPLOYEE.email, EMPLOYEE.password, /\/profile/);
    await expect(page).toHaveURL(/\/profile/);
  });

  test("login with wrong password shows error", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await page.getByLabel("Email").fill(ADMIN.email);
    await page.getByLabel("Пароль").fill("wrong");
    await page.getByRole("button", { name: "Войти" }).click();
    await expect(page.getByText("Invalid email or password")).toBeVisible();
  });
});

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.loginAndExpect(MANAGER.email, MANAGER.password, /\//);
  });

  test("shows employee count", async ({ page }) => {
    const dash = new DashboardPage(page);
    await expect(dash.totalEmployees()).toBeVisible();
  });

  test("shows skill coverage", async ({ page }) => {
    const dash = new DashboardPage(page);
    await expect(dash.skillCoverageTable()).toBeVisible();
  });

  test.skip("shows weakest skills section", async ({ page }) => {
    const dash = new DashboardPage(page);
    await expect(dash.hasWeakestSkills()).resolves.toBe(true);
  });

  test.skip("shows promotion ready section", async ({ page }) => {
    const dash = new DashboardPage(page);
    await expect(dash.hasPromotionReady()).resolves.toBe(true);
  });
});
