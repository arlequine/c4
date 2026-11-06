import { describe, it, expect, beforeEach } from 'vitest';
import {
  FeedbackInput,
  saveFeedback,
  listFeedback,
  resetFeedbackStore,
} from '../lib/feedback';

// FBK-01 · TASK-001 · Pruebas unitarias del esquema y el store.
// Spec: ../../docs/specs/FBK-01.md (v2). Cada test lleva el ID del CA o BR que cubre.

const ID_A = '11111111-1111-4111-8111-111111111111';
const ID_B = '22222222-2222-4222-8222-222222222222';

// ─── Esquema zod (TASK-001) ─────────────────────────────────────────────────

describe('FeedbackInput — validación', () => {
  it('acepta un voto válido con rating "up"', () => {
    expect(FeedbackInput.safeParse({ messageId: ID_A, rating: 'up' }).success).toBe(true);
  });

  it('acepta un 👎 con motivo de 200 caracteres', () => {
    const result = FeedbackInput.safeParse({ messageId: ID_A, rating: 'down', reason: 'x'.repeat(200) });
    expect(result.success).toBe(true);
  });

  it('CA-06 rechaza un rating que no es "up" ni "down"', () => {
    expect(FeedbackInput.safeParse({ messageId: ID_A, rating: 'meh' }).success).toBe(false);
  });

  it('CA-07 rechaza un motivo de 201 caracteres', () => {
    const result = FeedbackInput.safeParse({ messageId: ID_A, rating: 'down', reason: 'x'.repeat(201) });
    expect(result.success).toBe(false);
  });

  it('CA-08 rechaza un motivo junto con rating "up"', () => {
    const result = FeedbackInput.safeParse({ messageId: ID_A, rating: 'up', reason: 'no aplica' });
    expect(result.success).toBe(false);
  });

  it('CA-19 rechaza un messageId que no es uuid', () => {
    expect(FeedbackInput.safeParse({ messageId: 'abc', rating: 'up' }).success).toBe(false);
  });
});

// ─── Store en memoria (TASK-001) ────────────────────────────────────────────

describe('saveFeedback — un voto vigente por mensaje', () => {
  beforeEach(() => resetFeedbackStore());

  it('BR-FBK-01 el primer voto de un messageId devuelve replaced: false', () => {
    expect(saveFeedback({ messageId: ID_A, rating: 'up' })).toEqual({ replaced: false });
    expect(listFeedback()).toHaveLength(1);
  });

  it('BR-FBK-01 un segundo voto del mismo messageId reemplaza y no suma', () => {
    saveFeedback({ messageId: ID_A, rating: 'up' });
    expect(saveFeedback({ messageId: ID_A, rating: 'down' })).toEqual({ replaced: true });
    const all = listFeedback();
    expect(all).toHaveLength(1);
    expect(all[0].rating).toBe('down');
  });

  it('BR-FBK-03 el motivo se puede mandar después con un reemplazo', () => {
    saveFeedback({ messageId: ID_A, rating: 'down' });
    saveFeedback({ messageId: ID_A, rating: 'down', reason: 'faltó el precio' });
    expect(listFeedback()[0].reason).toBe('faltó el precio');
  });

  it('CA-18 al pasar de 👎 con motivo a 👍 se borra el motivo', () => {
    saveFeedback({ messageId: ID_A, rating: 'down', reason: 'x' });
    saveFeedback({ messageId: ID_A, rating: 'up' });
    const [record] = listFeedback();
    expect(record.rating).toBe('up');
    expect(record.reason).toBeUndefined();
  });

  it('votos de mensajes distintos se guardan por separado', () => {
    saveFeedback({ messageId: ID_A, rating: 'up' });
    saveFeedback({ messageId: ID_B, rating: 'down' });
    expect(listFeedback()).toHaveLength(2);
  });
});
