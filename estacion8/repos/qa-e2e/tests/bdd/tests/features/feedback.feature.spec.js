/** Generated from: tests/features/feedback.feature */
import { test } from "playwright-bdd";

test.describe("Calificar las respuestas del asistente (FBK-01)", () => {

  test("CA-15 Un voto negativo con motivo aparece en el panel", { tag: ["@TASK-006"] }, async ({ Given, page, And, When, Then }) => {
    await Given("que el responsable anotó los votos negativos del panel", null, { page });
    await And("que el usuario está en la página principal", null, { page });
    await When("el usuario envía el mensaje \"¿Qué servicios ofrecen?\"", null, { page });
    await And("el agente responde", null, { page });
    await And("el usuario califica la última respuesta como \"No me sirvió\" con el motivo \"faltó el precio\"", null, { page });
    await Then("el panel muestra un voto negativo más", null, { page });
    await And("el motivo más reciente del panel es \"faltó el precio\"", null, { page });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/features/feedback.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "CA-15 Un voto negativo con motivo aparece en el panel": {"pickleLocation":"8:3","tags":["@TASK-006"],"ownTags":["@TASK-006"]},
};