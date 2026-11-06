Feature: Calificar las respuestas del asistente (FBK-01)

  Como responsable del asistente
  Quiero que los usuarios califiquen las respuestas
  Para saber qué respuestas fallan y por qué

  @TASK-006
  Scenario: CA-15 Un voto negativo con motivo aparece en el panel
    Given que el responsable anotó los votos negativos del panel
    And que el usuario está en la página principal
    When el usuario envía el mensaje "¿Qué servicios ofrecen?"
    And el agente responde
    And el usuario califica la última respuesta como "No me sirvió" con el motivo "faltó el precio"
    Then el panel muestra un voto negativo más
    And el motivo más reciente del panel es "faltó el precio"
