import { test, expect } from '@playwright/test';
import { FeedbackApi } from '../../fixtures/feedback-builders';

// FBK-01 · API de calificaciones. Proyecto Playwright: `api` (sin paralelismo).
// Las stats se comparan como diferencias, nunca como valores absolutos (R-01, S-06).

test.describe('POST /api/feedback — guardar calificación', () => {
  test('CA-05 el primer voto válido de un mensaje responde 201 con replaced: false', { tag: '@TASK-002' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const res = await api.post(FeedbackApi.body({ rating: 'up' }));
    expect(res.status()).toBe(201);
    expect(await res.json()).toEqual({ ok: true, replaced: false });
  });

  test('CA-06 un rating distinto de up/down responde 400 con error', { tag: '@TASK-002' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const res = await api.post(FeedbackApi.body({ rating: 'meh' }));
    expect(res.status()).toBe(400);
    expect(await res.json()).toHaveProperty('error');
  });

  test('CA-06 un rating inválido no se guarda en las estadísticas', { tag: '@TASK-004' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const before = await api.stats();
    await api.post(FeedbackApi.body({ rating: 'meh' }));
    const after = await api.stats();
    expect(after.total - before.total).toBe(0);
  });

  test('CA-07 un motivo de 201 caracteres responde 400', { tag: '@TASK-002' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const res = await api.post(FeedbackApi.body({ rating: 'down', reason: 'x'.repeat(201) }));
    expect(res.status()).toBe(400);
  });

  test('CA-08 un motivo con rating up responde 400', { tag: '@TASK-002' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const res = await api.post(FeedbackApi.body({ rating: 'up', reason: 'no aplica' }));
    expect(res.status()).toBe(400);
  });

  test('CA-19 un messageId que no es uuid responde 400', { tag: '@TASK-002' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const res = await api.post(FeedbackApi.body({ messageId: 'abc' }));
    expect(res.status()).toBe(400);
  });

  test('un cuerpo que no es JSON válido responde 400', { tag: '@TASK-002' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const res = await api.postRaw('{no es json');
    expect(res.status()).toBe(400);
  });
});

test.describe('Doble voto y estadísticas', () => {
  test('CA-17 el segundo voto del mismo mensaje responde 200 con replaced: true', { tag: '@TASK-002' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const messageId = FeedbackApi.newMessageId();
    await api.post({ messageId, rating: 'up' });
    const res = await api.post({ messageId, rating: 'down' });
    expect(res.status()).toBe(200);
    expect(await res.json()).toEqual({ ok: true, replaced: true });
  });

  test('CA-17 un voto cambiado cuenta una sola vez en las estadísticas', { tag: '@TASK-004' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    const messageId = FeedbackApi.newMessageId();
    const before = await api.stats();
    await api.post({ messageId, rating: 'up' });
    await api.post({ messageId, rating: 'down' });
    const after = await api.stats();
    expect(after.total - before.total).toBe(1);
    expect(after.down - before.down).toBe(1);
    expect(after.up - before.up).toBe(0);
  });

  test('BR-FBK-04 GET /api/feedback/stats respeta el contrato', { tag: '@TASK-004' }, async ({ request }) => {
    const api = new FeedbackApi(request);
    await api.post(FeedbackApi.body({ rating: 'down', reason: 'contrato' }));
    const stats = await api.stats();
    expect(stats).toEqual({
      up: expect.any(Number),
      down: expect.any(Number),
      total: stats.up + stats.down,
      satisfaction: Math.round((stats.up / stats.total) * 100),
      lastReasons: expect.any(Array),
    });
    expect(stats.lastReasons.length).toBeLessThanOrEqual(5);
    expect(stats.lastReasons).toContainEqual({ reason: 'contrato', at: expect.any(String) });
  });
});
