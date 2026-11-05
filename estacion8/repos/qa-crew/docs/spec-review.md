# Spec review · `specs/escalamiento.md` (ESC · Escalar a un asesor humano)

Fecha: 2026-11-04 · Skill: `evaluate-spec` · Spec evaluada sin modificaciones.

Artefactos revisados:

- `qa-crew/specs/escalamiento.md` (la spec)
- `qa-e2e/demo-app/lib/agent.ts`, `qa-e2e/demo-app/app/api/chat/route.ts`
- `qa-e2e/demo-app/package.json`, `qa-e2e/package.json`, `qa-e2e/playwright.config.ts`
- `qa-e2e/steps/asistente.steps.ts`, `qa-e2e/tests/features/asistente.feature`,
  `qa-e2e/tests/e2e/flujo-principal.spec.ts`, `qa-e2e/demo-app/__tests__/agent.test.ts`
- `qa-agent-eval/personas/user-personas.md` (Carlos y Pedro)
- No existe `AGENTS.md` ni `design.md` en `qa-crew` ni en `qa-e2e` (registrado como vacío; `design.md` es N/A por la spec).

## 1. Notas por ola

| Ola | Nota | Justificación |
|---|---|---|
| Ola 1 · Detección de la intención | **A** | Reglas BR-ESC-01..04 identificables, CA-01..04 con entrada y salida exactas sobre una función pura, casos borde escritos y runner declarado. |
| Ola 2 · Experiencia en el chat | **A** | CA-05/06 observables en el navegador, steps reutilizables existentes y el sábado resuelto como regla (BR-ESC-07, l. 84-86) con su caso borde (l. 95-97). Revisado tras la corrección del 2026-11-04. |
| Ola 3 · Transferencia real a un asesor | **C** | El alcance existe, pero faltan reglas de negocio, proveedor, contrato y datos a enviar; CA-07 no es verificable tal como está. |

## 2. Recomendación

1. Planificar **Ola 1** primero (sin supuestos).
2. **Ola 2** puede planificarse junto a la Ola 1; ya no depende de supuestos.
3. **Ola 3** vuelve a diseño: elegir la herramienta de soporte y escribir reglas de cola, espera y fuera de horario antes de planificar.

## 3. Evaluación por lente

### Producto

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| P1 (*) Problema y usuario | Cumple | §1 (l. 5-13): cliente final del chat; hoy recibe el mensaje genérico. | — |
| P2 (*) Alcance | Cumple (O1, O2) / Parcial (O3) | «Alcance» de cada ola (l. 46, 76, 103). O3 dice *qué* pero no con qué herramienta. | O3: nombrar la herramienta o declarar un adaptador simulado para esta ronda. |
| P3 (*) Fuera de alcance | Cumple (O1, O2) / Parcial (O3) | §3 (l. 21-24): sin UI nueva, solo español. O3 no dice qué queda afuera (p. ej. fuera de horario, reintentos). | O3: listar explícitamente lo excluido. |
| P4 (*) Reglas de negocio | Cumple (O1, O2) / **Falta** (O3) | BR-ESC-01..06 (l. 51-58, 81-83). O3 l. 106-108: «No hay reglas sobre tiempos de espera, qué pasa fuera de horario ni qué datos se envían». | O3: escribir BR-ESC-07+ para cola, espera, fuera de horario y datos enviados. |
| P5 Criterio de éxito | Cumple | §2 (l. 15-19): ninguna petición recibe el genérico; Carlos y Pedro dejan de reprobar. Personas existen en `qa-agent-eval/personas/user-personas.md`. | Opcional: indicar el comando/reporte de Persona + Juez que se usará para medirlo. |
| P6 Decisiones pendientes | Cumple (O2) / Parcial (O3) | O2: sin pendientes; el horario del sábado quedó decidido en BR-ESC-07 (l. 84-86). O3 l. 106: «todavía no se eligió cuál» está en prosa, no como lista de preguntas. | O3: convertir la prosa en una lista «Pendientes» numerada. |

### TDD

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| T1 (*) Aceptación observable | Cumple (O1, O2) / **Falta** (O3) | Tablas CA-01..06 con textos exactos. CA-07 «ve su tiempo de espera» no dice formato, fuente ni valor esperado. | O3: definir qué texto/valor ve el usuario y cómo se simula la cola en pruebas. |
| T2 (*) Casos de prueba | Cumple (O1) / Cumple (O2) / **Falta** (O3) | O1: CA-01..04 + casos borde `Hola` y horarios (l. 69-70). O2: CA-05/06. O3: un solo caso feliz, sin errores ni bordes (fuera de horario, cola llena, fallo del proveedor). | O3: agregar casos de error y borde. |
| T3 Runner y comando | Cumple | §4 (l. 29-31). Verificado: `test:unit` = `vitest run` en `demo-app/package.json`; `test:bdd` = `bddgen && playwright test tests/bdd/` en `qa-e2e/package.json`; `baseURL` por defecto `http://localhost:3000` en `playwright.config.ts`. | Aclarar que ambos comandos se ejecutan desde `qa-e2e/`. |
| T4 Declaración TDD | Cumple | §4 l. 28: pruebas antes del código, deben fallar primero; ubicaciones declaradas. Regresión: 15 unitarios, 4 E2E, 4 escenarios BDD — conteos verificados en `agent.test.ts`, `flujo-principal.spec.ts` y `asistente.feature`. | — |

### Diseño

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| D1 (*) Arquitectura | Cumple (O1, O2) / **Falta** (O3) | §5 l. 37: `generateResponse()` en `lib/agent.ts`, función pura (verificado). O3 requiere integración externa, estado de cola y posiblemente polling o push; nada descrito. | O3: componente de integración, dónde vive el estado de la cola y cómo llega el tiempo de espera al cliente. |
| D2 Contratos | Cumple (O1, O2) / Falta (O3) | §5 l. 38: `POST /api/chat` → `{ response }` (verificado en `app/api/chat/route.ts`). O3 probablemente necesita campos nuevos (id de ticket, espera), lo que contradice «solo cambia el texto». | O3: definir el contrato nuevo o declarar que el tiempo de espera va dentro de `response`. |
| D3 design.md | N/A | §5 l. 40 y §3: sin cambios de interfaz. | O3: revisar si mostrar la espera exige UI; si sí, deja de ser N/A. |
| D4 Restricciones | Cumple (O1, O2) / Falta (O3) | §5 l. 39: sin datos personales nuevos. O3 enviaría la conversación (con nombre) a un tercero: datos personales, credenciales, latencia y disponibilidad sin definir. | O3: restricciones de datos personales, secretos y tiempos de respuesta. |

## 4. Coherencia entre artefactos

- **El trabajo ya avanzó más allá de la spec.** `qa-e2e/docs/tasks/` contiene `task-package.yaml`, `milestones.md`, `001-deteccion-intencion.md` y `002-respuesta-en-el-chat.md` (con O1 = A, O2 = B, O3 = C, coherente con esta revisión). Además, hay cambios sin commit en `qa-e2e/demo-app/lib/agent.ts` (rama de escalamiento, l. 63-67) y archivos nuevos sin seguimiento (`__tests__/escalamiento.test.ts`, `tests/features/escalamiento.feature`). La spec sigue diciendo «Estado: lista para revisión» (l. 3): conviene actualizarla.
- **Horario del escalamiento alineado con el código.** BR-ESC-07 (l. 84-86) coincide con lo que ya devuelve `agent.ts` l. 66. Las pruebas de la Ola 2 todavía no cubren el caso borde del sábado.
- **Dos horarios distintos para el usuario.** La respuesta de horarios (`agent.ts` l. 76) incluye sábados de 9:00 AM a 1:00 PM; la de escalamiento no. Ahora es una decisión explícita (BR-ESC-07), no un vacío.
- **Ola 1 y Ola 2 tocan la misma función.** BR-ESC-05 (horario) cambia el texto de `generateResponse()`, igual que la Ola 1; «Experiencia en el chat» no implica cambios de UI. Está bien, pero las tareas de O2 son sobre todo pruebas BDD.
- **Prioridad frente a la rama de «recall» no definida.** En `agent.ts` la rama de `recuerdas|cómo me llamo` va antes del escalamiento; BR-ESC-04 solo habla del saludo. Un mensaje como «¿Recuerdas mi nombre? Quiero hablar con un humano» no está cubierto.
- **Alcance de BR-ESC-01 con «agente».** La regla exige «agente real» o «agente humano»; «Quiero hablar con un agente» a secas no escala. Si es intencional, conviene agregarlo como caso borde negativo.
- **Ola 3 contradice el diseño común.** §5 dice «sin datos personales nuevos» y «solo cambia el texto»; transferir la conversación a una herramienta externa rompe ambas afirmaciones.
- **Rutas fuera del repo.** La spec vive en `qa-crew/specs/` pero todas las rutas apuntan al repo hermano `qa-e2e/` (`demo-app/lib/agent.ts`, `steps/asistente.steps.ts`, etc.). Verificado que existen; falta decir desde qué directorio se ejecutan los comandos.
- **Verificar:** la «herramienta de soporte del equipo» (O3, l. 106) no está identificada; no se puede confirmar que exponga cola o tiempos de espera.
- **Verificar:** el criterio de éxito depende de que Persona + Juez (`qa-agent-eval`) sea reproducible; los resultados de un LLM juez pueden variar entre corridas.

## 5. Los tres vacíos más graves

1. **Ola 3 sin reglas de negocio ni proveedor (P4, D1).** Sin esto no se puede ni descomponer en tareas: cada decisión la tendría que inventar el agente.
2. **CA-07 no verificable (T1, T2).** «Ve su tiempo de espera» no tiene valor esperado, ni doble de prueba para la cola, ni casos fuera de horario o de fallo.
3. **Caso borde del sábado sin prueba (Ola 2).** BR-ESC-07 ya está en la spec, pero ni `escalamiento.test.ts` ni `escalamiento.feature` fijan el reloj en un sábado.

## 6. Supuestos propuestos (pendientes de aprobación)

- ~~S-1 (Ola 2)~~: convertido en regla BR-ESC-07; ya no es un supuesto.
- **S-2 (Ola 1):** el escalamiento se evalúa después de la rama de «recall», como en el código actual; un mensaje que combine ambas cosas responde con el recall. *Pendiente de aprobación.*
- **S-3 (Ola 1):** «agente» sin «real» ni «humano» no dispara el escalamiento (caso borde negativo). *Pendiente de aprobación.*
- **S-4 (comandos):** `npm --prefix demo-app run test:unit` y `npm run test:bdd` se ejecutan desde `qa-e2e/`. *Pendiente de aprobación.*
- Ola 3: no se proponen supuestos; sus vacíos requieren trabajo de diseño y cuentan como **Falta**.
