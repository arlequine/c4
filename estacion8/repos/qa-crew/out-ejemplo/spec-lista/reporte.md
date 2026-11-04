# QA crew · reporte

- Spec: `specs/spec-lista.md`
- Modo: sin LLM (referencia)
- Fecha: 2026-11-03 23:39

## Resultado: VERDE en el intento 2

## 1 · Revisor de spec

Nota del código: **A** · nota del LLM: A. Detalle en `out/spec-review.md`.

## 2 · QA

Archivos: tests/features/escalamiento.feature

Fase rojo (`npm run test:bdd` antes del código): exit 1

## 3 + 4 · Desarrollo ↔ Ejecutor

| Intento | bdd | e2e | unit |
|---|---|---|---|
| 1 | ❌ (1) | ✅ | ✅ |
| 2 | ✅ | ✅ | ✅ |

### Falla del intento 1

```
  ✘  7 [bdd] › tests/bdd/tests/features/escalamiento.feature.spec.js:24:7 › Escalamiento a un asesor humano (ESC-01) › CA-03 El escalamiento tiene prioridad sobre el saludo (1.7s)
    Error: expect(received).toContain(expected) // indexOf
    Expected substring: "asesor humano"
    Received string:    "¡hola! soy el asistente virtual. ¿en qué puedo ayudarte hoy?"
    > 55 |   expect(respuesta.toLowerCase()).toContain(texto.toLowerCase());
    test-results/tests-features-escalamient-ae0d3-e-prioridad-sobre-el-saludo-bdd/test-failed-1.png
    Error Context: test-results/tests-features-escalamient-ae0d3-e-prioridad-sobre-el-saludo-bdd/error-context.md
  1 failed
  6 passed (16.3s)
```

## Diff en qa-e2e (revísalo tú; el crew no hace commit)

```diff
diff --git a/estacion8/repos/qa-e2e/demo-app/lib/agent.ts b/estacion8/repos/qa-e2e/demo-app/lib/agent.ts
index d80c17f..f9d2ca2 100644
--- a/estacion8/repos/qa-e2e/demo-app/lib/agent.ts
+++ b/estacion8/repos/qa-e2e/demo-app/lib/agent.ts
@@ -60,6 +60,12 @@ export function generateResponse(history: Message[], userMessage: string): strin
     return 'Lo siento, no tengo contexto previo sobre esa consulta.';
   }
 
+  // Escalamiento a un asesor humano (ESC-01)
+  if (/(hablar|comunicar(me)?|pasar(me)?)\s+con\s+(una?\s+)?(persona|humano|asesor|agente real)|(asesor|agente) humano/i.test(userMessage)) {
+    const saludo = name ? `Entendido, ${name}. ` : '';
+    return `${saludo}Te comunico con un asesor humano. Nuestro horario de atención es de lunes a viernes de 8:00 AM a 6:00 PM.`;
+  }
+
   // Saludo
   if (/^(hola|buenos días|buenas)/i.test(userMessage.trim())) {
     return '¡Hola! Soy el asistente virtual. ¿En qué puedo ayudarte hoy?';

--- archivo nuevo: tests/features/escalamiento.feature
Feature: Escalamiento a un asesor humano (ESC-01)

  Como cliente del chat de soporte
  Quiero poder pedir hablar con una persona
  Para no quedarme atorado con el asistente

  Background:
    Given que el usuario está en la página principal

  Scenario: CA-01 El asistente escala cuando el usuario pide una persona
    When el usuario envía el mensaje "Quiero hablar con una persona"
    Then la respuesta del agente menciona "asesor humano"
    And la respuesta del agente menciona "lunes a viernes de 8:00 AM a 6:00 PM"

  Scenario: CA-02 El asistente usa el nombre que ya conoce
    When el usuario envía el mensaje "Mi nombre es Ana"
    And el agente responde
    When el usuario envía el mensaje "Quiero hablar con un asesor"
    Then la respuesta del agente menciona "asesor humano"
    And la respuesta del agente menciona "Ana"

  Scenario: CA-03 El escalamiento tiene prioridad sobre el saludo
    When el usuario envía el mensaje "Hola, quiero hablar con un humano"
    Then la respuesta del agente menciona "asesor humano"

```
