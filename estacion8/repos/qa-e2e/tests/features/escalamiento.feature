Feature: Escalar a un asesor humano

  Como usuario del chat
  Quiero poder pedir hablar con una persona
  Para que me comuniquen con un asesor humano

  Background:
    Given que el usuario está en la página principal

  Scenario: CA-05 El usuario que pide una persona ve el asesor humano y el horario
    When el usuario envía el mensaje "Quiero hablar con una persona"
    Then la respuesta del agente menciona "asesor humano"
    And la respuesta del agente menciona "lunes a viernes de 8:00 AM a 6:00 PM"

  Scenario: CA-06 El escalamiento menciona el nombre que el usuario dijo antes
    When el usuario envía el mensaje "Mi nombre es Ana"
    And el agente responde
    When el usuario envía el mensaje "Quiero hablar con un asesor"
    Then la respuesta del agente menciona "asesor humano"
    And la respuesta del agente menciona "Ana"
