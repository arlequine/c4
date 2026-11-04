import { describe, it, expect } from 'vitest';
import { generateResponse, type Message } from '../lib/agent';

// TASK-001 · Ola 1 · Detección de la intención (TDD)
describe('Escalamiento a un asesor humano', () => {
  it('CA-01 reconoce "Quiero hablar con una persona"', () => {
    expect(generateResponse([], 'Quiero hablar con una persona')).toContain('asesor humano');
  });

  it('CA-02 reconoce variantes sin importar mayúsculas', () => {
    for (const mensaje of ['QUIERO HABLAR CON UN ASESOR', '¿Me pasas con un humano?', 'Necesito un agente real']) {
      expect(generateResponse([], mensaje)).toContain('asesor humano');
    }
  });

  it('CA-03 el escalamiento tiene prioridad sobre el saludo', () => {
    const respuesta = generateResponse([], 'Hola, quiero hablar con un humano');
    expect(respuesta).toContain('asesor humano');
    expect(respuesta).not.toContain('Soy el asistente virtual');
  });

  it('CA-04 usa el nombre que ya conoce', () => {
    const historial: Message[] = [
      { role: 'user', content: 'Mi nombre es Ana' },
      { role: 'agent', content: 'Gracias por tu mensaje.' },
    ];
    expect(generateResponse(historial, 'Quiero hablar con un asesor')).toMatch(/^Entendido, Ana\./);
  });
});
