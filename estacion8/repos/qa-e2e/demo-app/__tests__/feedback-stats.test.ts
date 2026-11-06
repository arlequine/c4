import { describe, it, expect, beforeEach } from 'vitest';
import { saveFeedback, listFeedback, resetFeedbackStore, type Feedback } from '../lib/feedback';
import { computeStats } from '../lib/feedback-stats';

// FBK-01 · TASK-004 · computeStats. Valores absolutos solo aquí (S-06).

function fb(partial: Partial<Feedback> & Pick<Feedback, 'messageId' | 'rating'>): Feedback {
  const at = partial.updatedAt ?? '2026-11-06T12:00:00.000Z';
  return { createdAt: at, updatedAt: at, ...partial };
}

describe('computeStats — estadísticas', () => {
  it('CA-09 con 3 👍 y 1 👎 devuelve totales y 75 % de satisfacción', () => {
    const stats = computeStats([
      fb({ messageId: 'a', rating: 'up' }),
      fb({ messageId: 'b', rating: 'up' }),
      fb({ messageId: 'c', rating: 'up' }),
      fb({ messageId: 'd', rating: 'down', reason: 'incompleta' }),
    ]);
    expect(stats).toMatchObject({ up: 3, down: 1, total: 4, satisfaction: 75 });
    expect(stats.lastReasons).toEqual([{ reason: 'incompleta', at: '2026-11-06T12:00:00.000Z' }]);
  });

  it('CA-10 sin calificaciones devuelve todo en cero', () => {
    expect(computeStats([])).toEqual({ up: 0, down: 0, total: 0, satisfaction: 0, lastReasons: [] });
  });

  it('CA-11 devuelve solo los 5 motivos más recientes, del más nuevo al más viejo', () => {
    const feedback = Array.from({ length: 7 }, (_, i) =>
      fb({
        messageId: `m${i}`,
        rating: 'down',
        reason: `motivo ${i}`,
        updatedAt: `2026-11-06T12:0${i}:00.000Z`,
      }),
    );
    const { lastReasons } = computeStats(feedback);
    expect(lastReasons.map((r) => r.reason)).toEqual(['motivo 6', 'motivo 5', 'motivo 4', 'motivo 3', 'motivo 2']);
  });

  it('BR-FBK-04 redondea la satisfacción al entero más cercano', () => {
    const stats = computeStats([
      fb({ messageId: 'a', rating: 'up' }),
      fb({ messageId: 'b', rating: 'up' }),
      fb({ messageId: 'c', rating: 'down' }),
    ]);
    expect(stats.satisfaction).toBe(67);
  });
});

describe('computeStats con el store', () => {
  beforeEach(() => resetFeedbackStore());

  it('CA-18 un motivo borrado al pasar a 👍 no aparece en lastReasons', () => {
    saveFeedback({ messageId: '11111111-1111-4111-8111-111111111111', rating: 'down', reason: 'x' });
    saveFeedback({ messageId: '11111111-1111-4111-8111-111111111111', rating: 'up' });
    expect(computeStats(listFeedback()).lastReasons).toEqual([]);
  });
});
