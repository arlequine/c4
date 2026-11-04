Feature: Escalamiento a un asesor humano (ESC-01)

  Como cliente del chat de soporte
  Quiero poder pedir hablar con una persona
  Para no quedarme atorado con el asistente

  Background:
    Given que el usuario está en la página principal

  Scenario: CA-01 El asistente escala cuando el usuario pide una persona
    When el usuario envía el mensaje "Quiero hablar con una persona"
    Then la respuesta del agente menciona "asesor humano"
    And la respuesta del agente menciona "lunes a viernes de 8:00 AM a 6:00 PM"

  Scenario: CA-02 El asistente usa el nombre que ya conoce
    When el usuario envía el mensaje "Mi nombre es Ana"
    And el agente responde
    When el usuario envía el mensaje "Quiero hablar con un asesor"
    Then la respuesta del agente menciona "asesor humano"
    And la respuesta del agente menciona "Ana"

  Scenario: CA-03 El escalamiento tiene prioridad sobre el saludo
    When el usuario envía el mensaje "Hola, quiero hablar con un humano"
    Then la respuesta del agente menciona "asesor humano"
