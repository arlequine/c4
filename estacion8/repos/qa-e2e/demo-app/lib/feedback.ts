/**
 * Dominio de FBK-01: calificaciones 👍/👎 de las respuestas del asistente.
 * Spec: docs/specs/FBK-01.md (v2) §4 y §6.
 */
import { z } from 'zod';

export type Rating = 'up' | 'down';

/** Calificación vigente de un mensaje del asistente (spec §6). */
export interface Feedback {
  messageId: string;
  rating: Rating;
  reason?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Esquema de entrada de `POST /api/feedback` (RF-03).
 * El motivo (1..200 caracteres) solo se acepta con `rating: "down"` (BR-FBK-02, CA-08).
 */
export const FeedbackInput = z
  .object({
    messageId: z.string().uuid(),
    rating: z.enum(['up', 'down']),
    reason: z.string().min(1).max(200).optional(),
  })
  .refine((input) => input.reason === undefined || input.rating === 'down', {
    message: 'El motivo solo se acepta con rating "down"',
    path: ['reason'],
  });

export type FeedbackInput = z.infer<typeof FeedbackInput>;

// Store en memoria guardado en globalThis para sobrevivir al hot reload de `next dev` (R-02).
const globalStore = globalThis as typeof globalThis & {
  __feedbackStore?: Map<string, Feedback>;
};

function store(): Map<string, Feedback> {
  if (!globalStore.__feedbackStore) {
    globalStore.__feedbackStore = new Map();
  }
  return globalStore.__feedbackStore;
}

/**
 * Guarda una calificación ya validada. Un voto vigente por `messageId`:
 * un segundo voto reemplaza al anterior (BR-FBK-01). Al pasar a 👍 el motivo
 * se borra (BR-FBK-02).
 */
export function saveFeedback(input: FeedbackInput): { replaced: boolean } {
  const records = store();
  const previous = records.get(input.messageId);
  const now = new Date().toISOString();

  const record: Feedback = {
    messageId: input.messageId,
    rating: input.rating,
    createdAt: previous?.createdAt ?? now,
    updatedAt: now,
  };
  if (input.rating === 'down' && input.reason !== undefined) {
    record.reason = input.reason;
  }

  records.set(input.messageId, record);
  return { replaced: previous !== undefined };
}

/** Devuelve las calificaciones vigentes, una por `messageId`. */
export function listFeedback(): Feedback[] {
  return Array.from(store().values(), (record) => ({ ...record }));
}

/** Vacía el store. Solo para pruebas: no se expone por HTTP. */
export function resetFeedbackStore(): void {
  store().clear();
}
