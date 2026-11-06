# Evaluación de spec · FBK-01 v2

Skill: `evaluate-spec`. Spec evaluada: `docs/specs/FBK-01.md` (v2, después de `improve-spec`, iteración 1). Fecha: 2026-11-06.
Review anterior: `docs/specs/FBK-01-review-v1.md` (C · C · C).

## 1. Notas por ola

| Ola | Alcance | v1 | **v2** | Por qué |
|---|---|---|---|---|
| 1 | Tipos/modelo `Feedback` + `POST /api/feedback` | C | **A** | BR-FBK-01..03 definen el upsert y el motivo. El contrato `201`/`200`/`400` está completo. CA-05..08, CA-17..19 son observables. |
| 2 | UI 👍/👎 + motivo · `GET /stats` · `/admin/feedback` | C | **A** | CA-12 ya es medible (testids + coherencia con `/stats`). Hay estado vacío (CA-14), cambio de voto (CA-16) y botón activo (CA-20). D3 queda en Parcial cerrado con S-04, pero no es crítico. |
| 3 | E2E + BDD del flujo calificar → panel | C | **B** | El flujo (CA-15) y el nivel de las pruebas (R-01, S-06) están definidos. Supuesto: los steps nuevos van en `steps/feedback.steps.ts`, porque la spec no lo dice. |

## 2. Recomendación

**Pasa a `create-implementation-plan`.** Planifica en orden Ola 1 → Ola 2 → Ola 3. Antes de crear issues en Linear, confirma los dos defaults de `improve-spec` (S-05 y S-06). Si cambias S-05 a `409`, solo cambian BR-FBK-01, CA-17 y el contrato `POST`.

## 3. Lentes

### Producto

| Criterio | Estado | Evidencia |
|---|---|---|
| P1 (*) Problema y usuario | Cumple | §1 |
| P2 (*) Alcance | Cumple | §3, RF-01..RF-06 |
| P3 (*) Fuera de alcance | Cumple | §3 (ahora incluye "quitar un voto") |
| P4 (*) Reglas de negocio | Cumple | §4 BR-FBK-01..05, sin contradicciones con RF-01 |
| P5 Criterio de éxito | Cumple | §2 |
| P6 Decisiones pendientes | Cumple | §8: P-01 resuelta; S-05 y S-06 marcados «confirmar» |

### TDD

| Criterio | Estado | Evidencia |
|---|---|---|
| T1 (*) Aceptación observable | Cumple | §5: 20 CA con nivel U/A/E, valores exactos o testids. CA-12 reescrito. |
| T2 (*) Casos de prueba | Cumple | Errores (CA-06/07/08/19), bordes (CA-04, CA-10, CA-14, CA-20), reemplazo (CA-17/18) |
| T3 Runner y comando | Cumple | §7 |
| T4 Declaración TDD | Cumple | §7 |

### Diseño

| Criterio | Estado | Evidencia |
|---|---|---|
| D1 (*) Arquitectura | Cumple | §6 Componentes (el panel es componente cliente para CA-14) |
| D2 Contratos | Cumple | §6 modelo `Feedback`, `POST` con `replaced`, `GET` con `lastReasons.at` |
| D3 design.md | Parcial → supuesto | S-04: reutilizar estilos de `page.tsx` |
| D4 Restricciones | Cumple | §6 Restricciones |

## 4. Coherencia entre artefactos

- CA-09/11 vs R-01: **resuelto**. Los valores absolutos quedan solo en `computeStats`, y API y E2E comparan diferencias.
- `npm run dev` de `demo-app` fija `-p 3000` en `package.json`. Para R-03, cada agente debe correr `npx next dev -p <puerto>` o `npm run dev -- -p <puerto>`. Hay que anotarlo en las tareas.
- Sigue sin existir `estacion6/ejemplos/spec-review-entrevista-ai.md`, el ejemplo que cita la skill. No afecta a la spec.

## 5. Vacíos que quedan

1. Ruta de los steps BDD nuevos (Ola 3): supuesto `steps/feedback.steps.ts`.
2. Confirmar los defaults S-05 (reemplazo) y S-06 (nivel de las pruebas de stats).
3. Puerto por agente: el script `dev` está fijo en 3000 (ver coherencia).

## 6. Supuestos pendientes de aprobación

- S-04, S-05 y S-06 (en la spec, §8).
- Steps BDD nuevos en `steps/feedback.steps.ts`.
