import { describe, it, expect, vi, afterEach } from 'vitest';
import { generateResponse, type Message } from '../lib/agent';

// ─── Escalamiento a un asesor humano (TASK-001 + TASK-002) ───────────────────
// TDD: estas pruebas se escriben ANTES del código. Deben fallar primero.

afterEach(() => {
  vi.useRealTimers();
});

describe('Escalamiento a asesor humano · generateResponse', () => {
  it('CA-01 pedir hablar con una persona responde con "asesor humano"', () => {
    const response = generateResponse([], 'Quiero hablar con una persona');
    expect(response).toContain('asesor humano');
  });

  it.each([
    'QUIERO HABLAR CON UN ASESOR',
    '¿Me pasas con un humano?',
    'Necesito un agente real',
  ])('CA-02 la intención se reconoce en el mensaje "%s"', (mensaje) => {
    const response = generateResponse([], mensaje);
    expect(response).toContain('asesor humano');
  });

  it('CA-03 "Hola, quiero hablar con un humano" responde escalamiento y no el saludo', () => {
    const response = generateResponse([], 'Hola, quiero hablar con un humano');
    expect(response).toContain('asesor humano');
    expect(response).not.toContain('asistente virtual');
  });

  it('CA-04 con nombre conocido la respuesta empieza con "Entendido, Ana."', () => {
    const history: Message[] = [{ role: 'user', content: 'Mi nombre es Ana' }];
    const response = generateResponse(history, 'Quiero hablar con un asesor');
    expect(response.startsWith('Entendido, Ana.')).toBe(true);
  });

  it('CA-05 borde sábado 10:00 AM: mismo texto que en día laborable, con horario fijo y sin "sábados"', () => {
    vi.useFakeTimers();

    vi.setSystemTime(new Date(2025, 0, 4, 10, 0)); // sábado 4 de enero de 2025, 10:00 AM
    const sabado = generateResponse([], 'Quiero hablar con una persona');

    vi.setSystemTime(new Date(2025, 0, 6, 10, 0)); // lunes 6 de enero de 2025, 10:00 AM
    const laborable = generateResponse([], 'Quiero hablar con una persona');

    expect(sabado).toContain('asesor humano');
    expect(sabado).toContain('lunes a viernes de 8:00 AM a 6:00 PM');
    expect(sabado).not.toContain('sábados');
    expect(sabado).toBe(laborable);
  });
});
