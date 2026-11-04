# QA crew · reporte

- Spec: `specs/escalamiento.md`
- Modo: sin LLM (referencia)
- Fecha: 2026-11-04 13:47

## Resultado: VERDE en el intento 2

## 1 · Olas (anthropic/claude-opus-5-5)

| Ola | Nota del código | Nota del LLM |
|---|---|---|
| ola-1 · Detección de la intención | **A** | A |
| ola-2 · Experiencia en el chat | **B** | B |
| ola-3 · Transferencia real a un asesor | **C** | C |

Detalle en `out/spec-review.md`.

## 2 · Plan (anthropic/claude-opus-5-5)

| Tarea | Título | Ola | Bloqueada por |
|---|---|---|---|
| TASK-001 | Detectar la intención de hablar con un asesor humano | ola-1 | — |
| TASK-002 | Mostrar en el chat la respuesta de escalamiento con horario y nombre | ola-2 | TASK-001 |

Paquete en `qa-e2e/docs/tasks/`.

## 3 a 5 · Matriz (pruebas: anthropic/claude-haiku-5-5 · desarrollo: anthropic/claude-sonnet-5-5 · ejecución: anthropic/claude-opus-5-5)

| Ola | CA | Estrategia | Prueba | Rojo antes | Verde después | Tarea | Cambio que lo cubre |
|---|---|---|---|---|---|---|---|
| ola-1 | CA-01 | TDD | `demo-app/__tests__/escalamiento.test.ts` | ❌ | ✅ | TASK-001 | La regex reconoce 'hablar con una persona' y la respuesta incluye 'asesor humano' |
| ola-1 | CA-02 | TDD | `demo-app/__tests__/escalamiento.test.ts` | ❌ | ✅ | TASK-001 | Flag /i para mayúsculas; 'pas\w* con' cubre 'me pasas con'; 'agente real' como alternativa |
| ola-1 | CA-03 | TDD | `demo-app/__tests__/escalamiento.test.ts` | ❌ | ✅ | TASK-001 | La regla quedó antes del bloque // Saludo, así que 'Hola, quiero…' escala |
| ola-1 | CA-04 | TDD | `demo-app/__tests__/escalamiento.test.ts` | ❌ | ✅ | TASK-001 | Prefijo `Entendido, ${name}. ` cuando extractName encuentra el nombre |
| ola-2 | CA-05 | BDD | `tests/features/escalamiento.feature` | ❌ | ✅ | TASK-002 | El texto de la respuesta incluye el horario fijo del supuesto |
| ola-2 | CA-06 | BDD | `tests/features/escalamiento.feature` | ❌ | ✅ | TASK-002 | El mismo prefijo con el nombre se ve en el chat |

## Intentos de desarrollo

| Intento | unit | bdd | e2e |
|---|---|---|---|
| 1 | ❌ (1) | ✅ | ✅ |
| 2 | ✅ | ✅ | ✅ |

### Falla del intento 1

```
 ❯ __tests__/escalamiento.test.ts (4 tests | 1 failed) 14ms
   × Escalamiento a un asesor humano > CA-03 el escalamiento tiene prioridad sobre el saludo 9ms
     → expected '¡Hola! Soy el asistente virtual. ¿En …' to contain 'asesor humano'
 Test Files  1 failed | 1 passed (2)
      Tests  1 failed | 18 passed (19)
 FAIL  __tests__/escalamiento.test.ts > Escalamiento a un asesor humano > CA-03 el escalamiento tiene prioridad sobre el saludo
AssertionError: expected '¡Hola! Soy el asistente virtual. ¿En …' to contain 'asesor humano'
Expected: "asesor humano"
Received: "¡Hola! Soy el asistente virtual. ¿En qué puedo ayudarte hoy?"
```

## Cambios en qa-e2e (revísalos tú; el crew no hace commit)

```diff
diff --git a/estacion8/repos/qa-e2e/demo-app/lib/agent.ts b/estacion8/repos/qa-e2e/demo-app/lib/agent.ts
index d80c17f..f57b3be 100644
--- a/estacion8/repos/qa-e2e/demo-app/lib/agent.ts
+++ b/estacion8/repos/qa-e2e/demo-app/lib/agent.ts
@@ -60,6 +60,12 @@ export function generateResponse(history: Message[], userMessage: string): strin
     return 'Lo siento, no tengo contexto previo sobre esa consulta.';
   }
 
+  // Escalamiento a un asesor humano (TASK-001 · BR-ESC-01..04, TASK-002 · BR-ESC-05..06)
+  if (/(hablar|comunicar\w*|pas\w*)\s+con\s+(una?\s+)?(persona|humano|asesor|agente real)|(asesor|agente) humano|agente real/i.test(userMessage)) {
+    const saludo = name ? `Entendido, ${name}. ` : '';
+    return `${saludo}Te comunico con un asesor humano. Nuestro horario de atención es de lunes a viernes de 8:00 AM a 6:00 PM.`;
+  }
+
   // Saludo
   if (/^(hola|buenos días|buenas)/i.test(userMessage.trim())) {
     return '¡Hola! Soy el asistente virtual. ¿En qué puedo ayudarte hoy?';

--- archivo nuevo: demo-app/__tests__/escalamiento.test.ts

--- archivo nuevo: docs/tasks/001-deteccion-intencion.md

--- archivo nuevo: docs/tasks/002-respuesta-en-el-chat.md

--- archivo nuevo: docs/tasks/milestones.md

--- archivo nuevo: docs/tasks/task-package.yaml

--- archivo nuevo: tests/features/escalamiento.feature

```
