import { test, expect, type Request } from '@playwright/test';
import { HomePage } from '../../pages/HomePage';
import { FeedbackPanelPage } from '../../pages/FeedbackPanelPage';

// FBK-01 · E2E de calificación de respuestas y panel. Spec: docs/specs/FBK-01.md (v2).
// Cada test lleva el ID del CA. Las stats reales se comparan contra /stats o como diferencias (R-01).

// Todo el archivo en orden y en un worker (mode default, sin saltar al fallar): comparte el store en memoria con el resto de pruebas (R-01).
test.describe.configure({ mode: 'default' });

const isFeedbackPost = (r: Request) => r.url().endsWith('/api/feedback') && r.method() === 'POST';

async function chatWithOneAnswer(home: HomePage, message = '¿Qué servicios ofrecen?') {
  await home.goto();
  await home.sendMessageAndWait(message);
}

// ─── Chat: botones y motivo (TASK-003) ──────────────────────────────────────

test.describe('FBK-01 · calificar respuestas en el chat', () => {
  test('CA-01 cada respuesta del asistente muestra los botones "Me sirvió" y "No me sirvió"', { tag: '@TASK-003' }, async ({ page }) => {
    const home = new HomePage(page);
    await chatWithOneAnswer(home);
    await expect(home.upButton()).toBeVisible();
    await expect(home.downButton()).toBeVisible();
  });

  test('CA-02 calificar con 👍 marca el botón y envía rating "up"', { tag: '@TASK-003' }, async ({ page }) => {
    const home = new HomePage(page);
    await chatWithOneAnswer(home);
    const post = page.waitForRequest(isFeedbackPost);
    await home.rate('up');
    const body = (await post).postDataJSON();
    expect(body).toMatchObject({ rating: 'up' });
    await expect(home.upButton()).toHaveAttribute('aria-pressed', 'true');
  });

  test('CA-03 calificar con 👎 muestra el campo de motivo vacío y el botón "Enviar motivo"', { tag: '@TASK-003' }, async ({ page }) => {
    const home = new HomePage(page);
    await chatWithOneAnswer(home);
    await home.rate('down');
    await expect(home.reasonInput()).toBeVisible();
    await expect(home.reasonInput()).toHaveValue('');
    await expect(home.reasonSubmit()).toBeVisible();
  });

  test('CA-04 el campo de motivo conserva como máximo 200 caracteres', { tag: '@TASK-003' }, async ({ page }) => {
    const home = new HomePage(page);
    await chatWithOneAnswer(home);
    await home.rate('down');
    await home.reasonInput().pressSequentially('x'.repeat(201));
    await expect(home.reasonInput()).toHaveValue('x'.repeat(200));
  });

  test('CA-13 calificar la segunda respuesta envía el messageId de la segunda', { tag: '@TASK-003' }, async ({ page }) => {
    const home = new HomePage(page);
    await chatWithOneAnswer(home, 'Hola');
    await home.sendMessageAndWait('¿Qué servicios ofrecen?');

    const first = page.waitForRequest(isFeedbackPost);
    await home.rate('up', 0);
    const firstId = (await first).postDataJSON().messageId;

    const second = page.waitForRequest(isFeedbackPost);
    await home.rate('up', 1);
    const secondId = (await second).postDataJSON().messageId;

    expect(firstId).toMatch(/^[0-9a-f-]{36}$/i);
    expect(secondId).toMatch(/^[0-9a-f-]{36}$/i);
    expect(secondId).not.toBe(firstId);
  });

  test('CA-16 cambiar de 👍 a 👎 invierte aria-pressed y muestra el motivo', { tag: '@TASK-003' }, async ({ page }) => {
    const home = new HomePage(page);
    await chatWithOneAnswer(home);
    await home.rate('up');
    await expect(home.upButton()).toHaveAttribute('aria-pressed', 'true');
    await home.rate('down');
    await expect(home.downButton()).toHaveAttribute('aria-pressed', 'true');
    await expect(home.upButton()).toHaveAttribute('aria-pressed', 'false');
    await expect(home.reasonInput()).toBeVisible();
  });

  test('CA-20 volver a hacer clic en el botón activo no envía otra calificación', { tag: '@TASK-003' }, async ({ page }) => {
    const home = new HomePage(page);
    await chatWithOneAnswer(home);
    const first = page.waitForRequest(isFeedbackPost);
    await home.rate('up');
    await first;

    const posts: Request[] = [];
    page.on('request', (r) => {
      if (isFeedbackPost(r)) posts.push(r);
    });
    await home.rate('up');
    await page.waitForTimeout(500); // ventana de observación: se espera que NO ocurra nada
    expect(posts).toHaveLength(0);
    await expect(home.upButton()).toHaveAttribute('aria-pressed', 'true');
  });
});

// ─── Panel con /stats simulado (TASK-005) ───────────────────────────────────

test.describe('FBK-01 · panel /admin/feedback con datos simulados', () => {
  test('CA-14 sin calificaciones el panel muestra el estado vacío', { tag: '@TASK-005' }, async ({ page }) => {
    await page.route('**/api/feedback/stats', (route) =>
      route.fulfill({ json: { up: 0, down: 0, total: 0, satisfaction: 0, lastReasons: [] } }),
    );
    const panel = new FeedbackPanelPage(page);
    await panel.goto();
    await expect(panel.emptyState).toHaveText('Aún no hay calificaciones');
    await expect(panel.reasonsList).toHaveCount(0);
  });

  test('CA-12 el panel muestra los valores de /stats y los motivos en el mismo orden (simulado)', { tag: '@TASK-005' }, async ({ page }) => {
    await page.route('**/api/feedback/stats', (route) =>
      route.fulfill({
        json: {
          up: 3,
          down: 1,
          total: 4,
          satisfaction: 75,
          lastReasons: [
            { reason: 'faltó el precio', at: '2026-11-06T12:01:00.000Z' },
            { reason: 'muy larga', at: '2026-11-06T12:00:00.000Z' },
          ],
        },
      }),
    );
    const panel = new FeedbackPanelPage(page);
    await panel.goto();
    expect(await panel.readStats()).toEqual({ up: 3, down: 1, total: 4, satisfaction: '75%' });
    expect(await panel.reasons()).toEqual(['faltó el precio', 'muy larga']);
  });
});

// ─── Integración real chat → panel (TASK-006) ───────────────────────────────

test.describe('FBK-01 · flujo real calificar → panel', () => {
  test('CA-12 el panel coincide con GET /api/feedback/stats', { tag: '@TASK-006' }, async ({ page }) => {
    const panel = new FeedbackPanelPage(page);
    await expect(async () => {
      await panel.goto();
      const shown = await panel.readStats();
      const api = await (await page.request.get('/api/feedback/stats')).json();
      expect(shown).toEqual({ up: api.up, down: api.down, total: api.total, satisfaction: `${api.satisfaction}%` });
      expect(await panel.reasons()).toEqual(api.lastReasons.map((r: { reason: string }) => r.reason));
    }).toPass({ timeout: 10_000 });
  });

  test('CA-15 un 👎 con motivo aparece en el panel', { tag: '@TASK-006' }, async ({ page }) => {
    const reason = `faltó el precio ${Date.now()}`;
    const before = await (await page.request.get('/api/feedback/stats')).json();

    const home = new HomePage(page);
    await chatWithOneAnswer(home);
    await home.rate('down');
    const post = page.waitForRequest((r) => isFeedbackPost(r) && r.postDataJSON()?.reason === reason);
    await home.submitReason(reason);
    await post;

    const panel = new FeedbackPanelPage(page);
    await panel.goto();
    const shown = await panel.readStats();
    expect(shown.down - before.down).toBe(1);
    await expect(panel.reasonItems.first()).toHaveText(reason);
  });
});
