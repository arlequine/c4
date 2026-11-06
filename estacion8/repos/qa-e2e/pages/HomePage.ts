import { Page, Locator } from '@playwright/test';

/**
 * Page Object: Página principal del asistente IA.
 * Encapsula todos los elementos y acciones de la interfaz de chat.
 */
export class HomePage {
  readonly page: Page;
  readonly chatInput: Locator;
  readonly sendButton: Locator;
  readonly latestAgentMessage: Locator;
  readonly loadingIndicator: Locator;
  // FBK-01 · calificación de respuestas
  readonly agentMessages: Locator;

  constructor(page: Page) {
    this.page = page;
    this.chatInput = page.getByRole('textbox', { name: /mensaje|escribe|message/i });
    this.sendButton = page.getByRole('button', { name: /enviar|send/i });
    this.latestAgentMessage = page.locator('[data-testid="agent-message"]').last();
    this.loadingIndicator = page.locator('[data-testid="loading"]');
    this.agentMessages = page.locator('[data-testid="agent-message"]');
  }

  async goto() {
    await this.page.goto('/');
  }

  async sendMessage(message: string) {
    await this.chatInput.fill(message);
    await this.sendButton.click();
  }

  async waitForResponse(): Promise<string> {
    await this.loadingIndicator.waitFor({ state: 'hidden', timeout: 15_000 });
    await this.latestAgentMessage.waitFor({ state: 'visible' });
    return (await this.latestAgentMessage.textContent()) ?? '';
  }

  async sendMessageAndWait(message: string): Promise<string> {
    await this.sendMessage(message);
    return this.waitForResponse();
  }

  // ─── FBK-01 · calificar respuestas ──────────────────────────────────────────
  // index: posición de la respuesta del asistente (0 = primera; -1 = última).

  agentMessage(index = -1): Locator {
    // nth(-1) apunta a la última respuesta.
    return this.agentMessages.nth(index);
  }

  upButton(index = -1): Locator {
    return this.agentMessage(index).getByRole('button', { name: 'Me sirvió' });
  }

  downButton(index = -1): Locator {
    return this.agentMessage(index).getByRole('button', { name: 'No me sirvió' });
  }

  reasonInput(index = -1): Locator {
    return this.agentMessage(index).getByPlaceholder('¿Qué faltó?');
  }

  reasonSubmit(index = -1): Locator {
    return this.agentMessage(index).getByRole('button', { name: 'Enviar motivo' });
  }

  async rate(rating: 'up' | 'down', index = -1) {
    await (rating === 'up' ? this.upButton(index) : this.downButton(index)).click();
  }

  async submitReason(text: string, index = -1) {
    await this.reasonInput(index).fill(text);
    await this.reasonSubmit(index).click();
  }
}
