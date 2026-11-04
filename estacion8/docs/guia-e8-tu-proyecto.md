# E8 · Llévalo a tu proyecto

**Objetivo de hoy:** que tu proyecto tenga **1 test E2E o de API** y **1 escenario BDD** en verde, que corran con un solo comando.
Entrega: **domingo 8 de noviembre**, antes de la E9. Sirve con cualquier stack que levante en un puerto local.

## Definition of Done (mínima)

- [ ] 1 test **E2E** (un flujo crítico, con Page Object) **o** 1 test de **API** (un endpoint, con request builder), en verde.
- [ ] 1 escenario **BDD**: un criterio de aceptación de tu spec de la E6 como `.feature` + steps, en verde.
- [ ] Los dos fallan si rompes a propósito lo que prueban (lo comprobaste una vez).
- [ ] Corren con **un solo comando** documentado en el README (por ejemplo `npm run test:e2e`).
- [ ] La URL de la app sale de una variable (`BASE_URL`), no está escrita en el test.
- [ ] Ningún `waitForTimeout` / `sleep`: se espera por estado o por elemento visible.

**Cómo entregar:** en el canal, el link al commit o PR y una captura del reporte en verde.

La meta completa de Andrés (tarea de la slide 25 de su deck) es más grande: 2 flujos E2E, 1 endpoint con contract tests y, si tu producto tiene un agente, Persona + Juez. Lo de arriba es el mínimo para el domingo.

---

## Antes de empezar

- Si tu app también usa el **puerto 3000**, apaga la `demo-app` del curso (`Ctrl+C`).
- Ten a la mano: tu **flujo crítico** (para el E2E), tu **endpoint** (para el de API) y **un criterio de aceptación** de tu spec E6 (para el BDD).
- El MCP de Playwright debe aparecer en `claude mcp list`. Si no:

```bash
npx -y playwright@1.64.0-alpha-1790635538000 install --with-deps chromium
claude mcp add --scope user playwright -- npx -y @playwright/mcp@0.0.83 --browser chromium
```

---

## Los 6 pasos

Los prompts van dentro de `claude`, abierto en la raíz de **tu** repo. Reemplaza lo que está entre `<>`.

### 1 · Levanta tu app y anota su URL

```bash
npm run dev          # o tu equivalente: uvicorn, ./gradlew bootRun, dotnet run, docker compose up…
export BASE_URL=http://localhost:<puerto>
```

### 2 · Instala Playwright (y BDD)

**Node / TypeScript:**

```bash
npm init playwright@latest        # elige TypeScript, carpeta tests/, sin GitHub Actions por ahora
npm i -D playwright-bdd           # para Gherkin
npx playwright install --with-deps chromium
```

**Otros stacks** (el MCP funciona igual porque mira el navegador, no tu código):

| Stack | Playwright | BDD |
|---|---|---|
| Python | `pip install pytest-playwright && playwright install chromium` | `pytest-bdd` |
| Java | dependencia `com.microsoft.playwright:playwright` | Cucumber-JVM |
| .NET | `Microsoft.Playwright` (NuGet) | Reqnroll |

Prompt si quieres que el agente lo haga:

```text
Configura Playwright en este repo para <lenguaje/stack>. Usa BASE_URL como baseURL (default http://localhost:<puerto>), solo Chromium, trace on-first-retry, screenshot only-on-failure. No agregues webServer. Deja un script "test:e2e" en <package.json / Makefile / README>. No toques código de la app.
```

### 3 · Copia el skill de QA y ajústalo

```bash
mkdir -p .claude/skills/qa-testing
cp ~/c4/estacion8/repos/qa-e2e/.claude/skills/qa-testing/SKILL.md .claude/skills/qa-testing/
```

```text
Lee .claude/skills/qa-testing/SKILL.md y ajústalo a este repo: rutas reales de carpetas (tests, pages, steps, features), el comando para correr las pruebas, el lenguaje y el framework. Mantén las reglas de POM primero, locators por rol y nada de waitForTimeout. Muéstrame el diff antes de guardar.
```

### 4 · Page Object primero, desde el DOM real

```text
Usa el MCP de Playwright para abrir <BASE_URL>/<ruta> y recorrer el flujo "<tu flujo crítico, paso a paso>". Con lo que veas, crea un Page Object en <pages/NombrePage.ts> siguiendo el skill qa-testing: locators por getByRole/getByLabel, métodos por acción del usuario. No escribas tests todavía.
```

Revisa que no haya selectores CSS por posición (`nth-child`, `div > div`). Si los hay, pídele que los cambie por rol o por `data-testid`.

### 5 · Un test E2E **o** uno de API

**E2E:**

```text
Escribe un test E2E en <tests/e2e/flujo-critico.spec.ts> que use el Page Object <NombrePage> para cubrir "<tu flujo>". Verifica el resultado que ve el usuario, no detalles internos. Córrelo y arréglalo hasta que pase, sin cambiar el código de la app ni debilitar los asserts.
```

**API:**

```text
Crea un request builder en <fixtures/request-builders.ts> para <METODO /ruta del endpoint> y un test en <tests/api/endpoint.spec.ts> que valide: status, forma de la respuesta (contrato: campos y tipos) y un caso de error (404 o 400). Usa el contexto request de Playwright con BASE_URL. Córrelo hasta que pase sin cambiar la app.
```

### 6 · Un escenario BDD desde tu spec de la E6

```text
Este es un criterio de aceptación de mi spec: "<pega el CA, por ejemplo CA-03 de docs/specs/...>". Escríbelo como Scenario en <tests/features/<nombre>.feature> (Given/When/Then en español) y crea los steps en <steps/<nombre>.steps.ts> reutilizando el Page Object. Configura playwright-bdd si falta (features, steps, outputDir). Antes de implementar nada, córrelo y muéstrame que falla o explícame por qué ya pasa.
```

Comandos (Node):

```bash
npx bddgen && npx playwright test     # o el script "test:bdd" que deje el agente
npx playwright show-report
```

---

## Comprueba que el test prueba algo

Rompe a propósito lo que cubre (cambia un texto, devuelve 500 en el endpoint) y córrelo: **debe ponerse rojo**. Regrésalo y debe volver a verde. Si sigue verde con la app rota, el test no está probando nada.

## Si te atoras

| Síntoma | Qué hacer |
|---|---|
| `Executable doesn't exist` | Falta el navegador: `npx playwright install --with-deps chromium` |
| Corren Firefox/WebKit y fallan | Limita a `--project=chromium` o deja solo Chromium en `projects` |
| El escenario nuevo no aparece | Te faltó `bddgen` antes de `playwright test` |
| `ECONNREFUSED localhost:3000` | La app no está corriendo, o está en otro puerto: revisa `BASE_URL` |
| El MCP no abre navegador en WSL | Agrega `--headless` al comando del MCP |
| El test pasa a veces | Busca `waitForTimeout` y esperas por tiempo; cámbialas por `expect(...).toBeVisible()` o por esperar un estado |
| El agente "arregló" el test cambiando el assert | Recházalo: el assert es la spec. Pídele que cambie el código o que te explique por qué el criterio está mal |
| Tu app no corre en local | Haz el test de API contra staging, **solo GET**, nunca producción con escrituras |

Dudas en el canal o en la tutoría del **jueves 5 de noviembre, 7 pm COT** (refuerzo E8). Lleguen con el error, no con "no me salió".
