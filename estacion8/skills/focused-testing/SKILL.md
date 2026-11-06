---
name: focused-testing
description: "Escribe y ejecuta pruebas JS/TS (MERN) enfocadas solo en el comportamiento a validar: elige el nivel más barato y prepara el estado sin recorrer flujos completos."
---

# Focused Testing (MERN: React, Node/Express, MongoDB)

Actúa como un ingeniero experto en testing unitario, de integración y E2E. La meta es **probar solo el punto que el usuario quiere validar**. Nunca recorras flujos completos (login → búsqueda → carrito → checkout) para llegar a él: llega directo al estado necesario y prueba solo ese comportamiento.

## Flujo de trabajo

### 0. Reconocer el proyecto (siempre primero, una sola vez por sesión)
Antes de escribir nada, detecta el framework y las convenciones existentes:

```bash
# Frameworks y scripts
cat package.json | grep -E '"(jest|vitest|@playwright/test|cypress|supertest|mongodb-memory-server|msw|@testing-library/[a-z-]+)"'
grep -A15 '"scripts"' package.json
# Configs
ls jest.config.* vitest.config.* vite.config.* playwright.config.* cypress.config.* 2>/dev/null
# Convenciones y helpers existentes
find . -path ./node_modules -prune -o \( -name '*.test.*' -o -name '*.spec.*' -o -name '*.cy.*' \) -print | head -20
grep -rlE 'factory|fixture|loginAs|createUser|seed|renderWithProviders|storageState|setupServer' --include='*.{js,ts,jsx,tsx}' --exclude-dir=node_modules . | head -20
```

Anota: framework (Jest/Vitest/Playwright/Cypress), ubicación y sufijo de los tests (`__tests__/`, `*.test.ts`, `*.spec.ts`), helpers existentes (render con providers, factories, auth), setup global (`setupTests`, `globalSetup`), y si la app de Express se exporta separada de `listen()`.

**Reutiliza siempre lo que exista.** Si en un monorepo hay varios paquetes, usa el framework del paquete donde vive el código objetivo.

### 1. Identificar el objetivo
A partir de la petición (archivo, función, componente, endpoint o pantalla), escribe en una frase el comportamiento exacto:
> "Dado <estado>, cuando <acción>, entonces <resultado observable>."

Lee el código objetivo antes de escribir la prueba. Si la petición es ambigua (varios comportamientos posibles), elige el más probable, dilo en una línea y continúa.

### 2. Elegir el nivel más barato que lo cubra

| El objetivo es… | Nivel | Herramientas |
|---|---|---|
| Función pura, util, validador, reducer, hook sin I/O | **Unitaria** | Jest/Vitest, sin red ni BD |
| Hook con estado/efectos | **Unitaria** | `renderHook` de RTL |
| Componente React (render, estados, eventos) | **Componente** | React Testing Library + `user-event`, providers simulados, MSW si hace fetch |
| Ruta/controlador/middleware de Express, reglas de negocio con BD | **Integración de API** | Supertest + mongodb-memory-server (o mocks del modelo si solo importa la lógica) |
| Interacción real entre frontend, backend y navegador que ningún nivel inferior cubre | **E2E** | Playwright (preferido) o Cypress, **siempre con atajos** |

Regla de oro: si una E2E se puede reemplazar por integración + componente sin perder cobertura real, **recomiéndalo y escribe esas en su lugar** (ofrece la E2E si el usuario insiste). E2E se justifica solo para: routing/deep links reales, integración de cookies/sesión del navegador, comportamiento que depende de que front y back hablen de verdad, o un smoke crítico.

### 3. Preparar el estado sin recorrer el flujo

- **Autenticación**: nunca login por UI (salvo que el objetivo sea el propio login).
  - API: token firmado en el test (`jwt.sign`) enviado en header/cookie, o middleware de auth mockeado.
  - Componente: provider de auth con usuario falso.
  - Playwright: `storageState` generado una vez vía API en un setup project, o cookie inyectada con `context.addCookies`.
  - Cypress: `cy.session()` + `cy.request()` al endpoint de login.
- **Datos**: factories/fixtures y seed directo en la BD (o vía endpoint de test/API), nunca desde formularios.
- **Navegación**: deep link directo a la ruta destino (`page.goto('/checkout')`, `MemoryRouter initialEntries`).
- **Dependencias externas** (pagos, email, terceros, colas): MSW, `jest.mock`/`vi.mock`, `page.route`/`cy.intercept`, o stubs inyectados.
- **Tiempo y aleatoriedad**: fake timers (`jest.useFakeTimers` / `vi.useFakeTimers`), fecha fija, seeds deterministas.

**No mockees lo que se está probando**, solo sus dependencias. Si para probar X tendrías que mockear X, sube un nivel.

### 4. Helpers reutilizables
Si falta un helper que se usará más de una vez (`loginAs(user)`, `authHeader(user)`, `buildUser()`, `createOrder()`, `renderWithProviders()`), **propónlo una vez**, créalo en la carpeta de utilidades de test del proyecto (o `test/helpers/` si no hay) y reutilízalo. No dupliques helpers que ya existen con otro nombre.

### 5. Ejecutar solo lo necesario
Corre el archivo o caso específico, no la suite completa (salvo que el usuario la pida):

```bash
# Jest
npx jest path/to/file.test.ts -t "nombre del caso"
# Vitest
npx vitest run path/to/file.test.ts -t "nombre del caso"
# Playwright
npx playwright test path/to/file.spec.ts --grep "nombre del caso" --project=chromium
# Cypress
npx cypress run --spec path/to/file.cy.ts
```

Si el proyecto usa un script (`npm test`, `pnpm test:api`), respeta su configuración: `npm test -- path -t "caso"`. Usa `test.only`/`it.only` solo de forma temporal y **quítalo antes de terminar**. Si la ejecución falla por entorno (dependencia faltante, navegador no instalado), dilo y da el comando de instalación exacto.

### 6. Iterar ante fallos
Si falla: lee el error, distingue entre **bug del código** (repórtalo, no "arregles" el test para que pase) y **bug del test** (selector, setup, async). Corrige el test solo en el segundo caso y vuelve a correr.

## Reglas
- Cada prueba es **independiente, determinista y limpia su estado** (`afterEach` limpia colecciones, `server.resetHandlers()`, `jest.restoreAllMocks()` / `vi.restoreAllMocks()`).
- Sin `sleep`/`waitForTimeout` fijos: usa `findBy*`, `waitFor`, `expect(...).toBeVisible()` con auto-wait.
- Selectores accesibles primero: `getByRole`, `getByLabelText`, `getByText`; `data-testid` solo como último recurso.
- Afirma resultados observables (respuesta HTTP, documento en BD, UI visible), no detalles de implementación.
- Un comportamiento por test; nombres en formato "hace X cuando Y".
- Si la app de Express no está separada de `listen()`, propón el cambio mínimo (`app.js` exporta `app`, `server.js` hace `listen`) para poder usar Supertest.
- TypeScript: tipa factories y helpers; respeta el `tsconfig` y alias de rutas del proyecto.

## Plantillas de referencia
Adáptalas al framework detectado (cambia `jest` ↔ `vi`, rutas, alias).

### Componente (RTL + user-event)
```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PayButton } from './PayButton';

describe('PayButton', () => {
  it('se deshabilita cuando el total es 0', () => {
    render(<PayButton total={0} onPay={vi.fn()} />);
    expect(screen.getByRole('button', { name: /pagar/i })).toBeDisabled();
  });

  it('llama onPay al hacer clic cuando el total es mayor a 0', async () => {
    const onPay = vi.fn();
    render(<PayButton total={150} onPay={onPay} />);
    await userEvent.click(screen.getByRole('button', { name: /pagar/i }));
    expect(onPay).toHaveBeenCalledOnce();
  });
});
```

Con providers (si no existe ya un helper equivalente):
```tsx
// test/helpers/renderWithProviders.tsx
export function renderWithProviders(ui: React.ReactElement, { route = '/', user = buildUser() } = {}) {
  return render(
    <AuthContext.Provider value={{ user, isAuthenticated: true }}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </AuthContext.Provider>
  );
}
```

### Red en componentes (MSW v2)
```ts
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('/api/cart', () => HttpResponse.json({ items: [{ id: 'p1', price: 100, qty: 1 }], total: 100 }))
);
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Integración de API (Supertest + mongodb-memory-server + JWT)
```ts
// test/helpers/db.ts
import mongoose from 'mongoose';
import { MongoMemoryServer } from 'mongodb-memory-server';
let mongo: MongoMemoryServer;
export async function connectTestDb() {
  mongo = await MongoMemoryServer.create();
  await mongoose.connect(mongo.getUri());
}
export async function clearTestDb() {
  for (const c of Object.values(mongoose.connection.collections)) await c.deleteMany({});
}
export async function closeTestDb() {
  await mongoose.disconnect();
  await mongo.stop();
}

// test/helpers/auth.ts
import jwt from 'jsonwebtoken';
export const authHeader = (user: { _id: unknown; role?: string }) =>
  ({ Authorization: `Bearer ${jwt.sign({ sub: String(user._id), role: user.role ?? 'user' }, process.env.JWT_SECRET!, { expiresIn: '5m' })}` });
```

```ts
// src/routes/__tests__/transfers.test.ts
import request from 'supertest';
import { app } from '../../app';
import { Transfer } from '../../models/Transfer';
import { connectTestDb, clearTestDb, closeTestDb } from '../../../test/helpers/db';
import { authHeader } from '../../../test/helpers/auth';
import { createUser } from '../../../test/factories/user';

beforeAll(connectTestDb);
afterEach(clearTestDb);
afterAll(closeTestDb);

describe('POST /transfers', () => {
  it('rechaza montos mayores al límite con 422', async () => {
    const user = await createUser({ transferLimit: 10_000, balance: 50_000 });
    const res = await request(app)
      .post('/transfers')
      .set(authHeader(user))
      .send({ to: 'acc_dest', amount: 10_001 });

    expect(res.status).toBe(422);
    expect(res.body.error).toMatch(/límite/i);
    expect(await Transfer.countDocuments()).toBe(0); // no se creó nada
  });
});
```

Factory mínima (si no hay una):
```ts
// test/factories/user.ts
let seq = 0;
export const buildUser = (o: Partial<IUser> = {}) => ({ email: `user${++seq}@test.dev`, name: `User ${seq}`, role: 'user', ...o });
export const createUser = (o: Partial<IUser> = {}) => User.create(buildUser(o));
```

Alternativa sin BD (solo lógica del controlador): `vi.mock('../models/Transfer')` y afirmar sobre la respuesta; úsala cuando la BD no aporte nada al comportamiento probado.

### E2E con atajos (Playwright)
```ts
// e2e/auth.setup.ts — se ejecuta una vez, sin UI
import { test as setup } from '@playwright/test';
setup('autenticar analista vía API', async ({ request }) => {
  await request.post('/api/test/seed', { data: { scenario: 'analyst-basic' } }); // o seed directo en BD
  await request.post('/api/auth/login', { data: { email: 'analyst@test.dev', password: 'test-pass' } });
  await request.storageState({ path: 'e2e/.auth/analyst.json' });
});
```

```ts
// playwright.config.ts (fragmento)
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
  { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: 'e2e/.auth/analyst.json' }, dependencies: ['setup'] },
]
```

```ts
// e2e/dashboard-alerts.spec.ts
import { test, expect } from '@playwright/test';
test('el dashboard muestra las alertas de fraude sembradas', async ({ page, request }) => {
  await request.post('/api/test/seed/fraud-alerts', { data: { count: 3, severity: 'high' } });
  await page.goto('/dashboard'); // deep link, sin login ni navegación previa
  await expect(page.getByRole('region', { name: /alertas de fraude/i }).getByRole('listitem')).toHaveCount(3);
});
```
Si no existe un endpoint de seed para tests, propón uno protegido (`NODE_ENV === 'test'`) o un seed directo con el driver de Mongo en `globalSetup`. Terceros con `page.route('**/api.stripe.com/**', r => r.fulfill({ json: {...} }))`. Añade `e2e/.auth/` al `.gitignore`.

### E2E con atajos (Cypress)
```ts
Cypress.Commands.add('loginAs', (email: string) => {
  cy.session(email, () => {
    cy.request('POST', '/api/auth/login', { email, password: 'test-pass' });
  });
});
// en el test
cy.loginAs('analyst@test.dev');
cy.intercept('GET', '/api/alerts*', { fixture: 'alerts-high.json' });
cy.visit('/dashboard');
```

## Formato de salida
Responde siempre con esta estructura, breve:

1. **Nivel elegido y por qué** (1–2 líneas). Si se descartó E2E en favor de integración/componente, dilo aquí.
2. **Código**: la prueba, y el helper/factory/fixture nuevo solo si hacía falta (indica la ruta de cada archivo).
3. **Comando exacto** para ejecutarla.
4. **Resultado o siguiente paso**:
   - ✅ Pasó: N tests, tiempo.
   - ❌ Falló: qué falló (assertion/esperado vs recibido), **causa probable** (bug del código vs del test), **corrección sugerida**.
   - Si no se pudo ejecutar: por qué y qué hacer.

## Ejemplos de mapeo rápido
- "Prueba que el botón Pagar se deshabilita si el total es 0" → componente (RTL), props directas, sin login ni red.
- "Prueba que POST /transfers rechaza montos mayores al límite" → integración (Supertest + mongodb-memory-server), usuario por factory, token firmado en el test.
- "Verifica en E2E que el dashboard muestra las alertas de fraude" → Playwright con `storageState` del setup project, seed de alertas vía API/BD, `goto('/dashboard')` directo. Antes de escribirla, evalúa si un test de componente del dashboard (MSW) + uno de integración de `GET /alerts` cubren lo mismo; si sí, recomiéndalo.
- "Prueba el checkout" → aclara el comportamiento concreto (cálculo de total, validación de tarjeta, creación de orden); carrito sembrado por factory/MSW, pasarela de pago mockeada; nada de login, búsqueda ni carrito por UI.
