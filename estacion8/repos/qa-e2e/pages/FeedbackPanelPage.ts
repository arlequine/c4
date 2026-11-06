import { Page, Locator } from '@playwright/test';

/**
 * Page Object: panel /admin/feedback (FBK-01, RF-05).
 * Testids definidos en docs/specs/FBK-01.md §6.
 */
export class FeedbackPanelPage {
  readonly page: Page;
  readonly statUp: Locator;
  readonly statDown: Locator;
  readonly statTotal: Locator;
  readonly statSatisfaction: Locator;
  readonly reasonsList: Locator;
  readonly reasonItems: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.statUp = page.getByTestId('stat-up');
    this.statDown = page.getByTestId('stat-down');
    this.statTotal = page.getByTestId('stat-total');
    this.statSatisfaction = page.getByTestId('stat-satisfaction');
    this.reasonsList = page.getByTestId('reasons-list');
    this.reasonItems = page.getByTestId('reason-item');
    this.emptyState = page.getByTestId('empty-state');
  }

  async goto() {
    await this.page.goto('/admin/feedback');
  }

  /** Espera a que el panel termine de cargar: o hay totales o hay estado vacío. */
  async waitForLoaded() {
    await this.statTotal.or(this.emptyState).first().waitFor({ state: 'visible' });
  }

  async readStats(): Promise<{ up: number; down: number; total: number; satisfaction: string }> {
    await this.waitForLoaded();
    const num = async (l: Locator) => Number((await l.textContent())?.trim());
    return {
      up: await num(this.statUp),
      down: await num(this.statDown),
      total: await num(this.statTotal),
      satisfaction: ((await this.statSatisfaction.textContent()) ?? '').trim(),
    };
  }

  async reasons(): Promise<string[]> {
    return (await this.reasonItems.allTextContents()).map((t) => t.trim());
  }
}
