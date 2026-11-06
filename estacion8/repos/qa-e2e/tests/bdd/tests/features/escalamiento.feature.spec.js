/** Generated from: tests/features/escalamiento.feature */
import { test } from "playwright-bdd";

test.describe("Escalar a un asesor humano", () => {

  test.beforeEach(async ({ Given, page }) => {
    await Given("que el usuario está en la página principal", null, { page });
  });

  test("CA-05 El usuario que pide una persona ve el asesor humano y el horario", async ({ When, page, Then, And }) => {
    await When("el usuario envía el mensaje \"Quiero hablar con una persona\"", null, { page });
    await Then("la respuesta del agente menciona \"asesor humano\"", null, { page });
    await And("la respuesta del agente menciona \"lunes a viernes de 8:00 AM a 6:00 PM\"", null, { page });
  });

  test("CA-06 El escalamiento menciona el nombre que el usuario dijo antes", async ({ When, page, And, Then }) => {
    await When("el usuario envía el mensaje \"Mi nombre es Ana\"", null, { page });
    await And("el agente responde", null, { page });
    await When("el usuario envía el mensaje \"Quiero hablar con un asesor\"", null, { page });
    await Then("la respuesta del agente menciona \"asesor humano\"", null, { page });
    await And("la respuesta del agente menciona \"Ana\"", null, { page });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/features/escalamiento.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "CA-05 El usuario que pide una persona ve el asesor humano y el horario": {"pickleLocation":"10:3"},
  "CA-06 El escalamiento menciona el nombre que el usuario dijo antes": {"pickleLocation":"15:3"},
};