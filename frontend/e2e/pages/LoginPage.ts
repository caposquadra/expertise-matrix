import { type Page } from "@playwright/test";

export class LoginPage {
  constructor(public readonly page: Page) {}

  async goto() {
    await this.page.goto("/login");
  }

  async login(email: string, password: string) {
    await this.page.getByLabel("Email").fill(email);
    await this.page.getByLabel("Пароль").fill(password);
    await this.page.getByRole("button", { name: "Войти" }).click();
  }

  async loginAndExpect(email: string, password: string, expectedUrl: RegExp) {
    await this.login(email, password);
    await this.page.waitForURL(expectedUrl);
  }

  async isLoggedIn() {
    return this.page.getByText("Дашборд").isVisible();
  }
}
