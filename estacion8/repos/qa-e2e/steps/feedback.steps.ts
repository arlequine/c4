import { createBdd } from 'playwright-bdd';
import { expect, type Page } from '@playwright/test';
import { HomePage } from '../pages/HomePage';
import { FeedbackPanelPage } from '../pages/FeedbackPanelPage';

// FBK-01 · steps del flujo calificar → panel. Reutiliza los steps de asistente.steps.ts.
const { Given, When, Then } = createBdd();

// Valor de stat-down antes de calificar, por página (cada escenario tiene su propia página).
const downBefore = new WeakMap<Page, number>();

Given('que el responsable anotó los votos negativos del panel', async ({ page }) => {
  const panel = new FeedbackPanelPage(page);
  await panel.goto();
  await panel.waitForLoaded();
  const visible = await panel.statDown.isVisible();
  downBefore.set(page, visible ? (await panel.readStats()).down : 0);
});

When(
  'el usuario califica la última respuesta como {string} con el motivo {string}',
  async ({ page }, etiqueta: string, motivo: string) => {
    const home = new HomePage(page);
    await home.rate(etiqueta === 'Me sirvió' ? 'up' : 'down');
    const post = page.waitForRequest(
      (r) => r.url().endsWith('/api/feedback') && r.method() === 'POST' && r.postDataJSON()?.reason === motivo,
    );
    await home.submitReason(motivo);
    await post;
  },
);

Then('el panel muestra un voto negativo más', async ({ page }) => {
  const panel = new FeedbackPanelPage(page);
  await panel.goto();
  const { down } = await panel.readStats();
  expect(down - (downBefore.get(page) ?? 0)).toBe(1);
});

Then('el motivo más reciente del panel es {string}', async ({ page }, motivo: string) => {
  const panel = new FeedbackPanelPage(page);
  await expect(panel.reasonItems.first()).toHaveText(motivo);
});
