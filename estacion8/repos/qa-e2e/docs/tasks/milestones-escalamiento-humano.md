# Project Milestones · escalamiento-humano

Spec de origen: **ESC · Escalar a un asesor humano** (asistente del chat de `qa-e2e/demo-app`).

Criterio de éxito global: ningún usuario que pida una persona recibe el mensaje
genérico ("Gracias por tu mensaje. He recibido tu consulta…"), y en la siguiente
corrida de Persona + Juez Carlos y Pedro dejan de reprobar por no poder escalar.

Fuera de alcance en todas las olas: cambios de interfaz (sin botones ni pantallas
nuevas) e idiomas distintos al español.

La Ola 3 (Transferencia real a un asesor, CA-07) **no está aprobada** y no forma
parte de esta planning wave.

## M1: Ola 1 · Detección de la intención

Goal: `generateResponse()` reconoce cuándo el usuario pide hablar con una persona
y responde con el escalamiento (texto `asesor humano`), aunque el mensaje empiece
con un saludo y personalizado con el nombre si se conoce. CA-01 a CA-04.

Tasks:

- TASK-001 Detectar la intención de hablar con un asesor humano en generateResponse()

## M2: Ola 2 · Experiencia en el chat

Goal: en el chat (navegador), quien pide una persona ve que lo van a comunicar con
un asesor humano, el horario fijo de atención (lunes a viernes de 8:00 AM a 6:00 PM)
y su nombre si lo dijo antes. CA-05 y CA-06. Depende de M1.

Tasks:

- TASK-002 Mostrar en el chat el escalamiento con horario fijo y nombre del usuario
