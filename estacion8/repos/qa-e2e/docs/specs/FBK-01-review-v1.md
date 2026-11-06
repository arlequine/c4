# Evaluación de spec · FBK-01 v1

Skill: `evaluate-spec`, copiada de `qa-crew/skills/evaluate-spec`. Spec evaluada: `docs/specs/FBK-01-v1.md`. Fecha: 2026-11-06.
Artefactos revisados: la spec, `README.md`, `demo-app/package.json`, `demo-app/app/page.tsx` y `playwright.config.ts`. No hay `design.md` ni `AGENTS.md`.

## 1. Notas por ola

| Ola | Alcance | Nota | Por qué |
|---|---|---|---|
| 1 | Tipos/modelo `Feedback` + `POST /api/feedback` (RF-03, RF-06) | **C** | No hay regla para un segundo voto del mismo `messageId` (P4). El store y el contrato `POST` no se pueden implementar sin adivinar si reemplaza, rechaza o suma. |
| 2 | Botones 👍/👎 + motivo (RF-01, RF-02) · `GET /stats` (RF-04) · `/admin/feedback` (RF-05) | **C** | CA-12 no es observable (T1). "Puede cambiar su voto" no tiene ningún CA. Cómo cuentan las stats un voto cambiado depende de la regla que falta en la Ola 1. |
| 3 | E2E + BDD del flujo calificar → panel | **C** | Hereda CA-12, porque no hay qué afirmar en el panel. CA-09 (conteos absolutos) choca con R-01 (comparar diferencias) y las pruebas en paralelo van a ser inestables. |

## 2. Recomendación

No planificar todavía. Las tres olas comparten la misma causa: falta una regla de negocio (el doble voto) y un CA medible para el panel. Se corrigen en la spec, sin trabajo de diseño nuevo, y después se vuelve a evaluar. Empieza por la Ola 1, porque su contrato define a las otras dos.

## 3. Lentes

### Producto

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| P1 (*) Problema y usuario | Cumple | §1: usuario final y responsable del asistente | — |
| P2 (*) Alcance | Cumple | §3 "Entra en esta ronda" + RF-01..RF-06 | — |
| P3 (*) Fuera de alcance | Cumple | §3 "Fuera de alcance" (5 puntos) | — |
| P4 (*) Reglas de negocio | **Falta** | §4 RF-01: "una sola vez" y "puede cambiar su voto" sin regla. No hay IDs BR-. §6 no dice qué hace un segundo `POST` del mismo `messageId`. | Agregar reglas BR-FBK-xx: unicidad por `messageId`, qué pasa al cambiar el voto, qué pasa con el motivo al pasar de 👎 a 👍 y cómo cuenta en las stats. |
| P5 Criterio de éxito | Cumple | §2: ≥ 1 de cada 5 respuestas calificadas y 3 motivos visibles | — |
| P6 Decisiones pendientes | Parcial | §8 lista P-01, pero el doble voto no aparece como pregunta | Resolver o listar el doble voto. |

### TDD

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| T1 (*) Aceptación observable | **Falta** (Ola 2/3) · Cumple (Ola 1, salvo doble voto) | §5 CA-12: "de forma clara y fácil de leer". RF-01 "cambiar su voto" no tiene CA. | Reescribir CA-12 con `data-testid` y valores exactos, más el estado vacío. Agregar CA de cambio de voto (UI y API). |
| T2 (*) Casos de prueba | Parcial | CA-05..CA-11 cubren errores de validación. Faltan: segundo voto, cambio 👎→👍 con motivo, `messageId` no uuid. | Agregar los CA de borde. |
| T3 Runner y comando | Cumple | §7: `npm --prefix demo-app run test:unit` y `npx playwright test --project=chromium --project=bdd` | — |
| T4 Declaración TDD | Cumple | §7 "TDD declarado" | — |

### Diseño

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| D1 (*) Arquitectura | Cumple | §6 Componentes: 5 archivos con su responsabilidad | — |
| D2 Contratos | Parcial | §6 Contratos `POST` y `GET`. Falta la respuesta a un segundo voto (¿201?, ¿200?, ¿409?). | Completar el contrato con el caso de reemplazo. |
| D3 design.md | Parcial | No existe `design.md`. Hay interfaz nueva (botones, motivo, panel). | Supuesto: reutilizar la paleta y los estilos en línea de `page.tsx` y no agregar librerías de UI. |
| D4 Restricciones | Cumple | §6 Restricciones: sin datos personales, `/admin` público y declarado | — |

## 4. Coherencia entre artefactos

- **CA-09 / CA-11 vs R-01:** los CA piden valores absolutos y el riesgo dice "comparar diferencias". Hay que decidir el nivel: valores absolutos en `computeStats` (unitarias) y diferencias en la API/E2E.
- **Verificar:** `zod` no está en `demo-app/package.json`. La spec ya lo declara como dependencia nueva (§6), así que es coherente.
- **Verificar:** `crypto.randomUUID()` en el navegador requiere contexto seguro. `http://localhost` cuenta como seguro, así que funciona en dev.
- La skill cita el ejemplo `estacion6/ejemplos/spec-review-entrevista-ai.md`, que **no existe** en la rama.
- La skill pide la salida en `docs/spec-review.md`. Por decisión del ejercicio, se guarda en `docs/specs/FBK-01-review*.md`.

## 5. Los tres vacíos más graves

1. **Regla del doble voto (P4):** bloquea el store, el contrato `POST`, las stats y la UI. Toca las tres olas.
2. **CA-12 no observable (T1):** el panel y el BDD final no tienen nada que afirmar.
3. **Nivel de las pruebas de stats (coherencia CA-09 vs R-01):** si no se decide, el E2E en paralelo va a ser inestable.

## 6. Supuestos propuestos (pendientes de aprobación)

- S-04: sin `design.md`, la interfaz reutiliza los estilos en línea y la paleta de `page.tsx`.
- Los demás vacíos son críticos y requieren una decisión, no un supuesto (los resuelve `improve-spec`).
