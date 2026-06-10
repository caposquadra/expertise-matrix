import { type Locator, type Page } from "@playwright/test";

export class DashboardPage {
  constructor(public readonly page: Page) {}

  async goto() {
    await this.page.goto("/");
  }

  totalEmployees(): Locator {
    return this.page.getByText("Всего сотрудников");
  }

  skillCoverageTable(): Locator {
    return this.page.getByText("Покрытие оценки по навыкам");
  }

  hasWeakestSkills() {
    return this.page.getByText("Самые слабые навыки").isVisible();
  }

  hasPromotionReady() {
    return this.page.getByText("Готовы к повышению").isVisible();
  }

  hasRecentChanges() {
    return this.page.getByText("Последние изменения").isVisible();
  }
}
