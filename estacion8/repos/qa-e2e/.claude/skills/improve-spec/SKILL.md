---
name: improve-spec
description: |
  Corrige una spec a partir del review de evaluate-spec hasta que sus olas
  lleguen a nota A o B. Solo toca los criterios en Falta o Parcial, hace como
  máximo 3 preguntas (cada una con un default) y vuelve a evaluar. Máximo 2
  iteraciones. Úsala después de evaluate-spec cuando alguna ola sale C o D.
---

# Improve Spec

## Propósito

Cerrar los vacíos que encontró `evaluate-spec` con el **cambio mínimo**, sin
reescribir la spec ni agregar alcance. La meta es que cada ola llegue a
**A** (todos los críticos cumplen) o **B** (los parciales cerrados con un
supuesto escrito).

## Entradas

- La spec: `docs/specs/<CLAVE>.md`.
- Su review más reciente: `docs/specs/<CLAVE>-review.md`, o
  `-review-v<N>.md` si se guardan versiones.
- El código del repo, solo para verificar nombres reales (archivos,
  `data-testid`, comandos). No para inventar requisitos.

Si falta el review, corre primero `evaluate-spec`. No adivines los vacíos.

## Proceso

1. **Inventario.** Del review, lista solo los criterios en **Falta** o
   **Parcial**, más los hallazgos de coherencia. Ignora los que están en
   Cumple.
2. **Clasifica cada vacío:**
   - **Se cierra con texto:** el review ya dice la corrección mínima y no
     requiere decidir nada. Por ejemplo, reescribir un CA vago con los
     `data-testid` que la propia spec define.
   - **Requiere una decisión de producto:** por ejemplo, qué pasa con un voto
     repetido. Va a pregunta.
   - **Se cierra con un supuesto:** solo para criterios **no críticos**, o
     parciales cuyo cierre no exige diseño. Se escribe como `S-xx`.
3. **Preguntas: máximo 3.** Cada una con:
   - la pregunta en una línea;
   - un **default** recomendado y por qué;
   - qué cambia en la spec si la respuesta es otra.

   Si el usuario no está o no contesta, aplica el default y regístralo como
   decisión tomada por default (sección de Supuestos, `S-xx`, con la nota
   «default de improve-spec, confirmar»).
4. **Edita la spec.** Toca solo las secciones que cierran vacíos:
   - reglas de negocio con ID `BR-<CLAVE>-NN`;
   - CA nuevos o reescritos, con ID consecutivo y sin renumerar los existentes;
   - contratos completados;
   - supuestos `S-xx` nuevos;
   - preguntas `P-xx` marcadas como resueltas, con la decisión.

   Sube el estado de la spec (`borrador v1` → `v2`) y agrega al final una
   sección **Cambios vN** con una línea por vacío cerrado, citando el
   criterio del review (por ejemplo, «P4: BR-FBK-01..04»).
5. **Re-evalúa** con `evaluate-spec` y guarda el resultado como un review
   nuevo. **No sobrescribas el anterior:** el contraste antes/después se
   muestra en clase.
6. **Itera como máximo 2 veces.** Si después de la segunda alguna ola sigue
   en C o D, detente y reporta qué vacío queda y por qué no se cerró. No
   bajes la vara del evaluador para pasar.

## Salida

- La spec actualizada.
- El review nuevo.
- Un resumen en el chat con una tabla `ola | nota antes | nota después`, las
  preguntas con la respuesta o el default aplicado, y los vacíos que quedaron.

## Reglas

- No agregues alcance. Si un vacío se cierra quitando algo, propónlo como
  pregunta.
- No cambies criterios que ya cumplen.
- No inventes nombres que el código o la spec no respalden. Si propones un
  `data-testid` nuevo, márcalo como nuevo en el CA.
- Un parcial en un criterio crítico solo se cierra con un supuesto si no
  exige diseño (la regla de `evaluate-spec`). Si exige diseño, es pregunta.
