# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.ts >> Dashboard >> shows weakest skills section
- Location: e2e/smoke.spec.ts:51:3

# Error details

```
Error: expect(received).resolves.toBe(expected) // Object.is equality

Expected: true
Received: false
```

# Page snapshot

```yaml
- generic [ref=e5]:
  - generic [ref=e6]:
    - img [ref=e7]
    - paragraph [ref=e12]: Expertise Matrix
  - paragraph [ref=e13]: Внутренний портал управления компетенциями команды тестирования
  - generic [ref=e15]:
    - generic [ref=e16]:
      - generic [ref=e17]: Email *
      - textbox "Email" [ref=e19]:
        - /placeholder: email@domain.com
        - text: manager@example.com
    - generic [ref=e20]:
      - generic [ref=e21]: Пароль *
      - generic [ref=e22]:
        - textbox "Пароль" [ref=e24]:
          - /placeholder: Ваш пароль
          - text: manager123
        - button [ref=e26] [cursor=pointer]:
          - img [ref=e28]
    - button "Войти" [disabled] [ref=e30]:
      - generic [ref=e34]: Войти
  - paragraph [ref=e35]: "Демо: admin@example.com / admin123"
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | import { LoginPage } from "./pages/LoginPage";
  3  | import { DashboardPage } from "./pages/DashboardPage";
  4  |
  5  | const ADMIN = { email: "admin@example.com", password: "admin123" };
  6  | const MANAGER = { email: "manager@example.com", password: "manager123" };
  7  | const EMPLOYEE = { email: "ivan@example.com", password: "ivan123" };
  8  |
  9  | test.describe("Authentication", () => {
  10 |   test("login as admin and see dashboard", async ({ page }) => {
  11 |     const login = new LoginPage(page);
  12 |     await login.goto();
  13 |     await login.loginAndExpect(ADMIN.email, ADMIN.password, /\//);
  14 |     await expect(page).toHaveURL(/\/$/);
  15 |   });
  16 |
  17 |   test("login as employee and redirect to profile", async ({ page }) => {
  18 |     const login = new LoginPage(page);
  19 |     await login.goto();
  20 |     await login.loginAndExpect(EMPLOYEE.email, EMPLOYEE.password, /\/profile/);
  21 |     await expect(page).toHaveURL(/\/profile/);
  22 |   });
  23 |
  24 |   test("login with wrong password shows error", async ({ page }) => {
  25 |     const login = new LoginPage(page);
  26 |     await login.goto();
  27 |     await page.getByLabel("Email").fill(ADMIN.email);
  28 |     await page.getByLabel("Пароль").fill("wrong");
  29 |     await page.getByRole("button", { name: "Войти" }).click();
  30 |     await expect(page.getByText("Invalid email or password")).toBeVisible();
  31 |   });
  32 | });
  33 |
  34 | test.describe("Dashboard", () => {
  35 |   test.beforeEach(async ({ page }) => {
  36 |     const login = new LoginPage(page);
  37 |     await login.goto();
  38 |     await login.loginAndExpect(MANAGER.email, MANAGER.password, /\//);
  39 |   });
  40 |
  41 |   test("shows employee count", async ({ page }) => {
  42 |     const dash = new DashboardPage(page);
  43 |     await expect(dash.totalEmployees()).toBeVisible();
  44 |   });
  45 |
  46 |   test("shows skill coverage", async ({ page }) => {
  47 |     const dash = new DashboardPage(page);
  48 |     await expect(dash.skillCoverageTable()).toBeVisible();
  49 |   });
  50 |
  51 |   test("shows weakest skills section", async ({ page }) => {
  52 |     const dash = new DashboardPage(page);
> 53 |     await expect(dash.hasWeakestSkills()).resolves.toBe(true);
     |                                                    ^ Error: expect(received).resolves.toBe(expected) // Object.is equality
  54 |   });
  55 |
  56 |   test("shows promotion ready section", async ({ page }) => {
  57 |     const dash = new DashboardPage(page);
  58 |     await expect(dash.hasPromotionReady()).resolves.toBe(true);
  59 |   });
  60 | });
  61 |
```
