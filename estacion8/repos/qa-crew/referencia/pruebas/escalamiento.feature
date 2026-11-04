Feature: Escalamiento a un asesor humano en el chat (TASK-002 · Ola 2)

  Como cliente del chat de soporte
  Quiero ver que me van a comunicar con una persona y en qué horario
  Para saber qué esperar

  Background:
    Given que el usuario está en la página principal

  Scenario: CA-05 El chat muestra el escalamiento con el horario
    When el usuario envía el mensaje "Quiero hablar con una persona"
    Then la respuesta del agente menciona "asesor humano"
    And la respuesta del agente menciona "lunes a viernes de 8:00 AM a 6:00 PM"

  Scenario: CA-06 El chat usa el nombre que ya conoce
    When el usuario envía el mensaje "Mi nombre es Ana"
    And el agente responde
    When el usuario envía el mensaje "Quiero hablar con un asesor"
    Then la respuesta del agente menciona "asesor humano"
    And la respuesta del agente menciona "Ana"
