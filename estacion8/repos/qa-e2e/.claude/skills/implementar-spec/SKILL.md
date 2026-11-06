---
name: implementar-spec
description: Prepara y guía el desarrollo de una feature a partir de una spec (docs/specs/<CLAVE>.md), en cualquier lenguaje o framework. Detecta el stack real del repo (o lo propone si el repo está vacío), genera los estándares de la feature, divide el trabajo en tareas trazadas a los CA y, tras la aprobación del usuario, escribe el código con TDD tarea por tarea. Úsala cuando el usuario pida implementar una spec o invoque /implementar-spec.
argument-hint: <ruta-spec> <ruta-tests | ninguno> <modelo>
---

# Implementar una spec con TDD (cualquier stack)

Argumentos recibidos: `$ARGUMENTS`

Trabajas en español. Los nombres de código (archivos, funciones, variables, pruebas) siguen la convención del lenguaje y del repo, aunque esté en inglés.

La spec es la fuente de verdad. No implementas nada que la spec no pida y no inventas datos que falten.

Esta skill no asume ningún lenguaje. Todo lo que dependa del stack (comandos, rutas, nombres, framework de pruebas) se **detecta en el repo** o, si el repo está vacío, se **propone y se aprueba** antes de escribir código.

---

## Fase 0 · Validar los argumentos

Separa `$ARGUMENTS` por espacios, en este orden:

| # | Argumento | Obligatorio | Valores válidos |
|---|-----------|-------------|-----------------|
| 1 | `ruta-spec` | Sí | Archivo `.md` existente, p. ej. `docs/specs/GRANO-142.md` |
| 2 | `ruta-tests` | Sí (posición) | Carpeta o archivo de pruebas existente, o `ninguno` |
| 3 | `modelo` | Sí | `opus`, `sonnet`, `haiku` u otro alias o ID de modelo |

**Si algo falla, detente, di exactamente qué falta y pide el dato. No lo supongas.**

- Falta `ruta-spec` o el archivo no existe → pide la ruta. Puedes listar `docs/specs/*.md`, pero no elijas por tu cuenta.
- Falta el segundo argumento → pregunta si hay pruebas o si va `ninguno`.
- `ruta-tests` no es `ninguno` y no existe → pide la ruta correcta.
- Falta `modelo` → pídelo. No uses el de la sesión como valor implícito.

**CLAVE** = nombre del archivo de la spec sin extensión (`docs/specs/GRANO-142.md` → `GRANO-142`).

---

## Fase 1 · Leer el contexto

### 1.1 Documentos

1. **Spec:** extrae los `RF-xx`, `CA-xx` y demás IDs (`S-xx`, `P-xx`, `R-xx`), lo que queda fuera de alcance, los supuestos y cualquier mención de tecnología (lenguaje, framework, base de datos, plataforma).
2. **Plan:** `<carpeta-spec>/<CLAVE>-plan.md`, si existe. Si no existe, lo dices y el desglose lo propones tú en la Fase 3.
3. **Revisión:** `<carpeta-spec>/<CLAVE>-review.md`, si existe. Si no dice "Listo", lo anotas como riesgo.
4. **`CLAUDE.md`** de la raíz y de las subcarpetas que toque la feature. Cuando sus reglas sean más estrictas que las de esta skill, mandan las suyas.

### 1.2 Detectar el stack (no asumir)

Busca **todos** los manifiestos (puede haber más de un lenguaje o un monorepo). Algunas señales habituales, sin que la lista sea cerrada:

| Ecosistema | Señales | Comando de pruebas típico (solo como pista) |
|------------|---------|---------------------------------------------|
| JavaScript / TypeScript | `package.json` + lockfile (`package-lock`, `pnpm-lock`, `yarn.lock`, `bun.lock*`), `deno.json`, `tsconfig.json` | script `test` del `package.json` |
| Python | `pyproject.toml`, `requirements*.txt`, `Pipfile`, `setup.py`, `uv.lock`, `poetry.lock` | `pytest` / `uv run pytest` |
| Go | `go.mod` | `go test ./...` |
| Rust | `Cargo.toml` | `cargo test` |
| Java / Kotlin | `pom.xml`, `build.gradle(.kts)`, `gradlew` | `mvn test` / `./gradlew test` |
| C# / .NET | `*.sln`, `*.csproj` | `dotnet test` |
| PHP | `composer.json` | `composer test` / `vendor/bin/phpunit` / `vendor/bin/pest` |
| Ruby | `Gemfile` | `bundle exec rspec` / `bin/rails test` |
| Elixir | `mix.exs` | `mix test` |
| Swift | `Package.swift`, `*.xcodeproj` | `swift test` |
| Dart / Flutter | `pubspec.yaml` | `dart test` / `flutter test` |
| C / C++ | `CMakeLists.txt`, `meson.build`, `Makefile` | `ctest` / target `test` |
| Otros | lo que encuentres | lo que definan sus herramientas |

**Orden de prioridad para elegir cada comando** (instalar, levantar, probar, una sola prueba, lint, formato, typecheck, build):

1. Lo que diga `CLAUDE.md` o el README.
2. Los *task runners* del repo: scripts de `package.json`, `Makefile`, `justfile`, `Taskfile.yml`, `composer.json` scripts, `[tool.*]`/`[project.scripts]` de `pyproject`, `mix` aliases, etc.
3. Lo que corre la CI (`.github/workflows/`, `.gitlab-ci.yml`, `azure-pipelines.yml`…).
4. El comando estándar del ecosistema (tabla de arriba), marcado como **"inferido"**.

Detecta también, con los archivos de configuración reales:
- El framework de pruebas (Vitest, Jest, pytest, JUnit, xUnit, RSpec, ExUnit, `testing` de Go…) y si hay pruebas E2E (Playwright, Cypress, Selenium…).
- El linter, el formateador y el typechecker (ESLint/Biome/Prettier, ruff/mypy, golangci-lint, clippy/rustfmt, Checkstyle/ktlint, dotnet format, PHPStan, RuboCop, Credo…).
- La librería de validación y la de logging que ya se usan.
- En monorepos, el paquete o servicio que toca la feature. Usa sus comandos, no los de la raíz.

**Verifica los comandos:** corre una vez el de pruebas (y el de lint/typecheck si existen) sin modificar nada, y registra el estado inicial. Si un comando falla porque falta instalar, dilo; instala solo si el comando de instalación ya está definido en el repo y no agrega dependencias nuevas. Lo que no exista se registra como **"no definido en el repo"**. No lo inventes.

### 1.3 Repo sin stack (proyecto nuevo)

Si no hay ningún manifiesto ni código fuente para la feature:

1. Busca el stack en la spec, el plan, la revisión y `CLAUDE.md`. Si está ahí, úsalo.
2. Si no está, inclúyelo entre las preguntas (ver 1.5) con un **default propuesto y justificado** por lo que pide la spec (tipo de app, plataforma, requisitos no funcionales). Ejemplo: "API HTTP con persistencia simple → default: TypeScript + Node 22 + Express + Vitest". El default se elige por lo que pide la spec, no por costumbre.
3. Planea una tarea **T00 · Base del proyecto** que:
   - Usa el inicializador oficial del ecosistema (`npm init`, `uv init`, `go mod init`, `cargo new`, `dotnet new`, `gradle init`, `composer init`, `bundle init`, `mix new`, `flutter create`…).
   - Configura el framework de pruebas, el linter y el formateador estándar del ecosistema.
   - Agrega una prueba humo (*smoke*) que pase.
   - Deja scripts o targets para `test`, `lint` y `dev` (o su equivalente).
   - Lista cada dependencia con su justificación para la aprobación de la Fase 4.

### 1.4 Pruebas y código existentes

- Si `ruta-tests` no es `ninguno`, lee esas pruebas para conocer el framework, el estilo, los helpers y los fixtures. Identifica qué CA ya cubren.
- Si es `ninguno`, revisa igual si el repo tiene pruebas en otro lado y copia su estilo.
- Abre 2 o 3 archivos del área que toca la feature para confirmar la estructura, los nombres y los patrones reales: inyección de dependencias, manejo de errores, capas.

### 1.5 Ambigüedades

Si algo bloquea el diseño (incluido el stack en un proyecto nuevo), haz **como máximo 5 preguntas**, todas juntas, cada una con su **default**:

```
1. [CA-03] ¿El descuento se aplica antes o después del envío?
   → Default: antes del envío (coincide con RF-02).
2. [Stack] El repo está vacío y la spec no fija tecnología.
   → Default: Python 3.12 + FastAPI + pytest + ruff (API HTTP pequeña, validación con pydantic).
```

Si el usuario responde "ok" o "usa los defaults", aplicas los defaults. Lo que no bloquea, no lo preguntes: va como supuesto en los estándares.

---

## Fase 2 · Generar los estándares

Crea `docs/standards/<CLAVE>-estandares.md` (y la carpeta, si hace falta) con `plantilla-estandares.md`, que está junto a este archivo. Llena todas las secciones con lo detectado; nada genérico:

1. **Stack y comandos:** los comandos exactos, cada uno marcado como **verificado**, **inferido** o **no definido**.
2. **Estructura:** dónde va cada tipo de archivo y las convenciones de nombres del lenguaje y del repo.
3. **Estilo de código:** tipado (o anotaciones/contratos si el lenguaje es dinámico), manejo de errores idiomático del lenguaje (excepciones, `Result`, `error` de Go…), validación de entradas con la librería del repo y logging.
4. **Testing:** TDD rojo → verde → refactor, al menos una prueba por cada `CA-xx` y cómo se corren las pruebas existentes.
5. **Trazabilidad:** formato de commit y de nombre de prueba con los IDs (ver la tabla de abajo), más la matriz CA → prueba → tarea.
6. **Límites del agente** (sección "Límites", tal cual).
7. **Definition of Done.**
8. **Modelo asignado** y sus recomendaciones.
9. **Supuestos y decisiones.**

### Cómo llevar el ID del CA en la prueba, según el lenguaje

Usa el mecanismo idiomático del framework detectado:

| Framework | Forma |
|-----------|-------|
| Jest / Vitest / Mocha / Playwright | `it("CA-02: aplica el descuento al subtotal", …)` |
| pytest | `def test_ca_02_aplica_descuento_al_subtotal():` |
| Go `testing` | `func TestCA02_AplicaDescuento(t *testing.T)` o `t.Run("CA-02: …", …)` |
| Rust | `#[test] fn ca_02_aplica_descuento()` |
| JUnit 5 | `@DisplayName("CA-02: …") void ca02_aplicaDescuento()` |
| xUnit / NUnit | `[Fact(DisplayName = "CA-02: …")]` / `[Test, Description("CA-02: …")]` |
| RSpec / Minitest | `it "CA-02: …"` / `test "CA-02: …"` |
| PHPUnit / Pest | `#[TestDox('CA-02: …')]` / `it('CA-02: …')` |
| ExUnit | `test "CA-02: …"` |
| Otro | el nombre de la prueba o su descripción debe contener `CA-xx` |

**Commit:** respeta la convención del repo (`git log` reciente) y añade la CLAVE y los IDs. Si no hay una, usa `feat(<CLAVE>): <qué> [RF-xx, CA-xx]`.

Este es el único archivo que escribes antes de la aprobación.

---

## Fase 3 · Dividir en tareas

A partir del plan (si existe) o de los RF y CA de la spec:

- **Pequeñas y verificables:** cada tarea termina con al menos una prueba que pasa de rojo a verde.
- **Ordenadas por dependencia:** (T00 base del proyecto, si aplica) → tipos/modelos y validación → lógica de dominio → borde de entrada/salida (API, CLI, UI, persistencia) → integración/E2E.
- **Trazadas:** qué RF/CA cubre cada una y con qué prueba se valida.
- **Todo CA queda cubierto.** Si un CA no se puede automatizar, márcalo y propone cómo verificarlo.

Formato (las rutas y comandos son los del repo real):

```
T03 · <título>
  Cubre: RF-02, CA-03
  Depende de: T01, T02
  Prueba: <archivo de prueba> → "<nombre con CA-03>"
  Archivos: <ruta> (nuevo), <ruta> (modificar)
  Verificación: <comando para correr solo esa prueba>
```

Si `ruta-tests` es `ninguno`, antes de las tareas pon la **propuesta de pruebas**: por cada CA, el nombre de la prueba, el archivo, el escenario (dado / cuando / entonces) y el resultado esperado.

Si hay pruebas existentes, indica qué CA cubren, cuáles faltan y su estado inicial.

Agrega la matriz CA → prueba → tarea a los estándares.

---

## Fase 4 · Resumen y aprobación (único punto de control)

Muestra:

- Spec, CLAVE, plan y revisión (encontrados o no).
- Stack detectado o propuesto, y los comandos (verificado / inferido / no definido).
- Ruta de los estándares generados.
- Pruebas existentes (estado inicial) o propuestas.
- Tareas: ID, título y CA que cubre cada una.
- Dependencias nuevas con su justificación (en un proyecto nuevo, las de T00), o "ninguna".
- Supuestos y riesgos.
- Modelo asignado. Si no coincide con el de la sesión, sugiere `/model <modelo>` antes de implementar.

Termina con esta pregunta y **detente**:

> ¿Apruebas los estándares, las dependencias y el plan de tareas para empezar a escribir código? Puedes pedirme cambios antes.

La aprobación cubre todo lo listado: con un "sí" empiezas a programar de inmediato y no vuelves a preguntar en cada tarea, salvo por algo que no estaba en el resumen (otra dependencia, un archivo fuera de alcance, un cambio a la spec).

---

## Fase 5 · Escribir el código, tarea por tarea

Empieza en cuanto haya aprobación. Para cada tarea, en orden:

1. **Rojo:** escribe la prueba de la tarea, con el CA en el nombre. Córrela y confirma que **falla por la razón esperada**: falta la función o el comportamiento, no un error de sintaxis ni de configuración. Si pasa sin cambios, detente y explica por qué.
2. **Verde:** escribe el código mínimo e idiomático para el lenguaje y el repo. Toca solo los archivos que declara la tarea.
3. **Verifica:** la prueba de la tarea, la suite del área afectada, y lint, formato y typecheck si existen. En lenguajes compilados, también que compile.
4. **Refactor:** limpia sin cambiar el comportamiento y vuelve a correr todo.
5. **Reporta:**

```
T03 · <título> — ✅
  CA cubiertos: CA-03
  Pruebas: <N> passed, 0 failed (<comando>)
  Lint/typecheck: limpio
  Archivos: <ruta> (+42), <ruta> (+8 −2)
  Commit sugerido: feat(<CLAVE>): <qué> [RF-02, CA-03]
```

**Regla de avance:** no pasas a la siguiente tarea si la actual no está completamente en verde.

Si algo queda en ❌:
- Hasta **2 intentos** de corrección, explicando el cambio en cada uno.
- Si sigue en rojo, detente con la salida real del error y tu diagnóstico, y pregunta cómo seguir.
- Nunca desactives, saltes ni debilites pruebas (`skip`, `xfail`, `@Ignore`, `#[ignore]`, aserciones relajadas) para llegar a verde.

**Commits:** si `CLAUDE.md` o los permisos lo permiten, haz un commit local por tarea. Si no, deja el mensaje sugerido en el reporte.

---

## Fase 6 · Cierre

1. Corre la suite completa y lint/typecheck/build una última vez.
2. Verifica la Definition of Done punto por punto.
3. Actualiza la matriz de trazabilidad con el estado final.
4. Si algo cambió respecto a la spec, propone el cambio exacto y aplícalo solo con aprobación.
5. Resumen final: tareas ✅, CA cubiertos, archivos tocados, commits y pendientes.

---

## Límites (no negociables)

- Sin `git push`, sin merge ni rebase a `main`, sin `reset --hard` ni reescritura de historial.
- Sin borrar archivos: propón el borrado y deja que lo haga el usuario.
- No leas, crees ni modifiques `.env`, `.env.*`, llaves, certificados, tokens ni otros secretos. Si hace falta una variable nueva, documéntala en los estándares con un valor ficticio.
- Solo modificas lo que pide la spec. Lo que veas fuera de alcance va como sugerencia.
- **Dependencias:** ninguna nueva sin justificarla (qué resuelve y por qué no alcanza con lo que ya hay) y sin aprobación explícita.
- Nada contra producción ni servicios reales (pagos, correo, APIs de terceros): usa mocks, fakes o el entorno local.

---

## Ajuste por modelo

Escribe el nivel de detalle en la sección 8 de los estándares y aplícalo al plan de tareas.

| Modelo | Tamaño de tarea | Instrucciones | Recomendaciones |
|--------|-----------------|---------------|-----------------|
| `opus` | Media: 2–3 CA relacionados, varios archivos | Objetivo, criterios y restricciones; margen para el diseño interno | Pedir que justifique las decisiones; útil para lógica con muchas reglas y refactors |
| `sonnet` | Pequeña: 1–2 CA, hasta 3 archivos | Pasos numerados con archivos y comandos concretos | Revisar los casos borde que menciona la spec |
| `haiku` | Atómica: 1 CA, 1–2 archivos | Pasos cortos: archivo exacto, firma exacta, prueba exacta, comando exacto y resultado esperado | Nada implícito; repetir las restricciones en cada tarea; detenerse ante cualquier duda |
| otro | Igual que `sonnet` | Indicarlo en los estándares | Ajustar tras la primera tarea |

Con modelos más pequeños, el plan deja decididos de antemano los nombres, las firmas y las rutas, para que la implementación no tenga que inventar nada.
