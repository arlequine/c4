/**
 * FBK-01 · Dominio de calificaciones de respuestas del asistente.
 * Tipos, esquema de entrada (zod) y store en memoria con un voto vigente por mensaje.
 * Spec: docs/specs/FBK-01.md §4 (BR-FBK-01, BR-FBK-02) y §6 (contratos).
 */
import { z } from 'zod';

export type Rating = 'up' | 'down';

export interface Feedback {
  messageId: string;
  rating: Rating;
  reason?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Esquema de entrada de `POST /api/feedback`.
 * `reason` va de 1 a 200 caracteres y solo se acepta con `rating: "down"` (CA-06, CA-07, CA-08, CA-19).
 */
export const FeedbackInput = z
  .object({
    messageId: z.uuid({ error: 'messageId debe ser un uuid' }),
    rating: z.enum(['up', 'down'], { error: 'rating debe ser "up" o "down"' }),
    reason: z
      .string()
      .min(1, { error: 'El motivo no puede estar vacío' })
      .max(200, { error: 'El motivo admite como máximo 200 caracteres' })
      .optional(),
  })
  .refine((input) => input.reason === undefined || input.rating === 'down', {
    error: 'El motivo solo se acepta con rating "down"',
    path: ['reason'],
  });

export type FeedbackInput = z.infer<typeof FeedbackInput>;

const globalStore = globalThis as typeof globalThis & {
  __fbk01FeedbackStore?: Map<string, Feedback>;
};

/** Store en `globalThis` para que sobreviva al hot reload de `next dev` (spec §6). */
function store(): Map<string, Feedback> {
  if (!globalStore.__fbk01FeedbackStore) {
    globalStore.__fbk01FeedbackStore = new Map();
  }
  return globalStore.__fbk01FeedbackStore;
}

/**
 * Guarda una calificación ya validada. Si el `messageId` ya tenía voto, lo reemplaza
 * (BR-FBK-01) y conserva `createdAt`. El motivo solo se guarda con 👎 (BR-FBK-02).
 */
export function saveFeedback(input: FeedbackInput): { replaced: boolean } {
  const feedback = store();
  const previous = feedback.get(input.messageId);
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

  feedback.set(input.messageId, record);
  return { replaced: previous !== undefined };
}

/** Devuelve las calificaciones vigentes, una por `messageId`. */
export function listFeedback(): Feedback[] {
  return Array.from(store().values());
}

/** Vacía el store. Solo para pruebas: no se expone por HTTP. */
export function resetFeedbackStore(): void {
  store().clear();
}
