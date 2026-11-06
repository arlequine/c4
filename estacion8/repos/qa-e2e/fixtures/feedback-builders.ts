import { APIRequestContext, APIResponse } from '@playwright/test';
import { randomUUID } from 'node:crypto';

/**
 * Request builder para la API de FBK-01 (skill qa-testing §5: nada de request.post suelto).
 * Contratos: docs/specs/FBK-01.md §6.
 */
export type Rating = 'up' | 'down';

export interface FeedbackBody {
  messageId?: unknown;
  rating?: unknown;
  reason?: unknown;
}

export interface FeedbackStats {
  up: number;
  down: number;
  total: number;
  satisfaction: number;
  lastReasons: { reason: string; at: string }[];
}

export class FeedbackApi {
  constructor(private readonly request: APIRequestContext) {}

  static newMessageId(): string {
    return randomUUID();
  }

  /** Cuerpo válido por defecto; cada campo se puede sobrescribir para probar errores. */
  static body(overrides: FeedbackBody = {}): FeedbackBody {
    return { messageId: FeedbackApi.newMessageId(), rating: 'up', ...overrides };
  }

  post(body: FeedbackBody): Promise<APIResponse> {
    return this.request.post('/api/feedback', { data: body });
  }

  postRaw(raw: string): Promise<APIResponse> {
    return this.request.post('/api/feedback', {
      data: raw,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  async stats(): Promise<FeedbackStats> {
    const res = await this.request.get('/api/feedback/stats');
    if (!res.ok()) throw new Error(`GET /api/feedback/stats respondió ${res.status()}`);
    return res.json();
  }
}
