"""QA crew · E8 bonus.

Spec → olas evaluadas → plan de implementación → pruebas TDD/BDD → desarrollo → ejecución + match.

  1. Revisor de spec     Opus    skill evaluate-spec          la nota de cada ola la recalcula el código
  2. Planificador        Opus    skill create-implementation-plan   el paquete lo valida el código (paso 6 de la skill)
  3. Diseñador de pruebas Haiku  skill qa-testing             TDD (Vitest) o BDD (Gherkin) según el CA; deben fallar primero
  4. Desarrollador       Sonnet  trabaja desde el paquete de tareas; solo demo-app/lib/agent.ts
  5. Ejecutor            Opus    corre las suites y explica el match; el veredicto por CA sale de los reportes JSON

Uso:
  uv run crew --spec specs/escalamiento.md               # con Claude (ANTHROPIC_API_KEY)
  uv run crew --spec specs/escalamiento.md --pausar      # se detiene entre etapas (para clase)
  uv run crew --spec specs/escalamiento.md --sin-llm     # plan B: respuestas de referencia/, pruebas reales
  uv run crew --reset                                    # deja qa-e2e y out/ como estaban
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from crewai.flow.flow import Flow, listen, router, start

from .gate import RevisionSpec, calcular_nota, cas_por_ola, cobertura, pasa, supuestos, veredicto_por_ca
from .plan import validar_paquete
from .tools import CorrerPruebas, EscribirArchivo, LeerArchivo, Registro, correr_suite

AQUI = Path(__file__).resolve().parents[2]  # qa-crew/
REF = AQUI / "referencia"
OUT = AQUI / "out"
SKILLS = AQUI / "skills"

MODELOS_DEFECTO = {
    "revisor": "anthropic/claude-opus-5-5",
    "plan": "anthropic/claude-opus-5-5",
    "pruebas": "anthropic/claude-haiku-5-5",
    "dev": "anthropic/claude-sonnet-5-5",
    "ejecutor": "anthropic/claude-opus-5-5",
}
ETAPAS = {"revisor": "1 · Revisor de spec", "plan": "2 · Planificador", "pruebas": "3 · Diseñador de pruebas",
          "dev": "4 · Desarrollador", "ejecutor": "5 · Ejecutor"}

PLAN_PERMITIDAS = ("docs/tasks/*.md", "docs/tasks/*.yaml")
QA_PERMITIDAS = ("tests/features/*.feature", "steps/*.steps.ts", "demo-app/__tests__/*.test.ts")
QA_PROTEGIDAS = ("tests/features/asistente.feature", "steps/asistente.steps.ts", "demo-app/__tests__/agent.test.ts")
DEV_PERMITIDAS = ("demo-app/lib/agent.ts",)
VIGILADOS = ("tests/features", "steps", "demo-app/__tests__")
SUITES_ROJO = ("unit", "bdd")
SUITES_VERDE = ("unit", "bdd", "e2e")


def modelo(etapa: str) -> str:
    return os.environ.get(f"QA_MODEL_{etapa.upper()}", MODELOS_DEFECTO[etapa])


def log(msg: str) -> None:
    print(f"[qa-crew {datetime.now():%H:%M:%S}] {msg}", flush=True)


def cargar_env() -> None:
    f = AQUI / ".env"
    if not f.exists():
        return
    for linea in f.read_text().splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def qa_e2e_dir() -> Path:
    return (AQUI / os.environ.get("QA_E2E_DIR", "../qa-e2e")).resolve()


def huella(root: Path) -> str:
    h = hashlib.sha256()
    for d in VIGILADOS:
        for p in sorted((root / d).rglob("*")):
            if p.is_file():
                h.update(str(p.relative_to(root)).encode())
                h.update(p.read_bytes())
    return h.hexdigest()


# ───────────────────────── estado y salidas estructuradas

class FilaMatriz(BaseModel):
    ca: str = Field(description="CA-01, CA-02, …")
    estrategia: str = Field(description="TDD o BDD")
    archivo: str = Field(description="Archivo de prueba donde quedó")


class MatrizPruebas(BaseModel):
    filas: list[FilaMatriz]


class FilaMatch(BaseModel):
    ca: str
    tarea: str = Field(description="TASK-00X del paquete")
    cambio: str = Field(description="Qué parte del cambio en agent.ts cubre este CA (línea o regla), en una frase")


class Match(BaseModel):
    filas: list[FilaMatch]
    resumen: str = ""


class Estado(BaseModel):
    spec_path: str = ""
    spec_texto: str = ""
    sin_llm: bool = False
    pausar: bool = False
    max_reintentos: int = 2
    olas: list[dict] = []
    olas_pasan: dict[str, str] = {}
    cas: dict[str, list[str]] = {}
    plan_errores: list[str] = []
    tareas: list[dict] = []
    matriz: list[dict] = []
    rojo: dict = {}
    intentos: list[dict] = []
    match: dict = {}
    final: str = ""
    alertas: list[str] = []
    tokens: dict[str, dict] = {}


# ───────────────────────── agentes (solo con LLM)

def _llm(etapa: str):
    from crewai import LLM

    # Los modelos Claude 5 ya no aceptan `temperature` (la API responde 400).
    return LLM(model=modelo(etapa))


def _skill(nombre: str):
    from crewai.skills import activate_skill, discover_skills

    return [activate_skill(s) for s in discover_skills(SKILLS) if s.frontmatter.name == nombre]


def agente(etapa: str, root: Path, registro: Registro | None = None):
    from crewai import Agent

    comunes = dict(llm=_llm(etapa), allow_delegation=False, max_iter=15)
    if etapa == "revisor":
        return Agent(role="Revisor de spec", goal="Calificar cada ola de la spec con la skill evaluate-spec, con evidencia citada.",
                     backstory="Revisas specs antes de planificar. No apruebas un criterio sin evidencia.",
                     skills=_skill("evaluate-spec"), tools=[LeerArchivo(root)], **comunes)
    if etapa == "plan":
        return Agent(role="Planificador", goal="Convertir las olas aprobadas en un paquete de tareas con la skill create-implementation-plan.",
                     backstory="Tus tareas las ejecuta otro agente sin acceso a este chat: todo lo que necesita va escrito.",
                     skills=_skill("create-implementation-plan"),
                     tools=[LeerArchivo(root), EscribirArchivo(root, PLAN_PERMITIDAS)], **comunes)
    if etapa == "pruebas":
        return Agent(role="Diseñador de pruebas", goal="Escribir, antes del código, las pruebas TDD o BDD de cada criterio de aceptación.",
                     backstory="Sigues la skill qa-testing. Lógica pura va con unitarias; lo que ve el usuario va con Gherkin.",
                     skills=_skill("qa-testing"),
                     tools=[LeerArchivo(root), EscribirArchivo(root, QA_PERMITIDAS, QA_PROTEGIDAS)], **comunes)
    if etapa == "dev":
        return Agent(role="Desarrollador", goal="Implementar las tareas del plan hasta que pasen las pruebas, cambiando solo demo-app/lib/agent.ts.",
                     backstory="Trabajas con TDD: las pruebas son la especificación. Nunca modificas una prueba para que pase.",
                     tools=[LeerArchivo(root), EscribirArchivo(root, DEV_PERMITIDAS)], **comunes)
    return Agent(role="Ejecutor", goal="Correr las suites pedidas y explicar qué parte del código cubre cada criterio.",
                 backstory="Eres el último filtro. Reportas hechos: prueba, resultado y cambio que la cubre.",
                 tools=[CorrerPruebas(root, registro), LeerArchivo(root)], **comunes)


# ───────────────────────── flow

class QACrewFlow(Flow[Estado]):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.root = qa_e2e_dir()
        self.registro = Registro()

    # utilidades ────────────────────────────────────────────────────────
    def tarea(self, etapa: str, descripcion: str, esperado: str, output_pydantic=None, registro: Registro | None = None):
        from crewai import Crew, Task

        ag = agente(etapa, self.root, registro)
        t = Task(description=descripcion, expected_output=esperado, agent=ag, output_pydantic=output_pydantic)
        r = Crew(agents=[ag], tasks=[t], verbose=True).kickoff()
        uso = getattr(r, "token_usage", None)
        acc = self.state.tokens.setdefault(etapa, {"modelo": modelo(etapa), "entrada": 0, "salida": 0})
        if uso is not None:
            acc["entrada"] += int(getattr(uso, "prompt_tokens", 0) or 0)
            acc["salida"] += int(getattr(uso, "completion_tokens", 0) or 0)
        return r, ag

    def pausa(self, texto: str) -> None:
        if self.state.pausar and sys.stdin.isatty():
            input(f"\n⏸  {texto} · Enter para seguir… ")

    def correr(self, suites: tuple[str, ...], contexto: str) -> dict[str, int]:
        """El ejecutor (Opus) corre las suites; el veredicto sale del registro, no de su texto."""
        inicio = len(self.registro.ejecuciones)
        if not self.state.sin_llm:
            self.tarea("ejecutor", f"{contexto}\nCorre, en este orden, las suites: {', '.join(suites)}. "
                       "Después resume en máximo 10 líneas qué pruebas fallaron, con lo esperado y lo obtenido. No propongas código.",
                       "Resumen de fallas o 'todo en verde'.", registro=self.registro)
        corridas = {e.suite: e for e in self.registro.ejecuciones[inicio:]}
        for s in suites:
            if s not in corridas:
                if not self.state.sin_llm:
                    self.state.alertas.append(f"El ejecutor no corrió '{s}'; lo corrió el flow.")
                corridas[s] = correr_suite(self.root, s, self.registro)
        return {s: corridas[s].exit_code for s in suites}

    def resultados(self, suites: tuple[str, ...]):
        out = []
        for s in suites:
            e = self.registro.ultima(s)
            if e:
                out += e.resultados
        return out

    def todos_los_cas(self) -> list[str]:
        return [ca for ola in self.state.olas_pasan for ca in self.state.cas.get(ola, [])]

    # 1 · Revisor ───────────────────────────────────────────────────────
    @start()
    def revisar_spec(self):
        log(f"{ETAPAS['revisor']} · {modelo('revisor')} · {self.state.spec_path}")
        self.state.cas = cas_por_ola(self.state.spec_texto)
        if self.state.sin_llm:
            rev = RevisionSpec.model_validate_json((REF / "revision.json").read_text())
            log("   (sin LLM: referencia/revision.json)")
        else:
            olas = ", ".join(self.state.cas) or "las que encuentres"
            r, _ = self.tarea(
                "revisor",
                "Evalúa esta spec con la skill evaluate-spec, UNA NOTA POR OLA. Las olas son las secciones '## Ola N' "
                f"({olas}); usa id 'ola-N'. Las secciones 1 a 5 son comunes a todas las olas. Para cada ola evalúa los 14 "
                "criterios (P1–P6, T1–T4, D1–D4) como Cumple, Parcial, Falta o N/A, con la sección que lo respalda. Si un "
                "crítico es Parcial y la spec propone un supuesto que lo cierra, cópialo en 'supuesto'. No escribas archivos: "
                "devuelve solo el JSON.\n\n--- SPEC ---\n" + self.state.spec_texto,
                "Un JSON RevisionSpec con una entrada por ola.", output_pydantic=RevisionSpec)
            rev = r.pydantic
        for ola in rev.olas:
            nota, razones = calcular_nota(ola.criterios)
            fila = {"id": ola.id, "nombre": ola.nombre, "nota": nota, "nota_llm": ola.nota_llm, "razones": razones,
                    "supuestos": supuestos(ola), "vacios": ola.vacios_graves,
                    "criterios": [c.model_dump() for c in ola.criterios]}
            self.state.olas.append(fila)
            if nota != ola.nota_llm:
                self.state.alertas.append(f"{ola.id}: el LLM puso {ola.nota_llm}, el código calcula {nota}. Manda el código.")
            if pasa(nota):
                self.state.olas_pasan[ola.id] = nota
            log(f"   {ola.id} · {ola.nombre}: nota {nota} (LLM: {ola.nota_llm}) → {'pasa' + (' con supuestos' if nota == 'B' else '') if pasa(nota) else 'vuelve a diseño'}")
        escribir_spec_review(self.state)
        self.pausa("Revisión lista (out/spec-review.md)")

    @router(revisar_spec)
    def compuerta_olas(self):
        return "hay_olas" if self.state.olas_pasan else "ninguna_ola"

    @listen("ninguna_ola")
    def detener(self):
        self.state.final = "DETENIDO · ninguna ola tiene A o B: la spec vuelve a diseño"
        cerrar(self)

    # 2 · Planificador ──────────────────────────────────────────────────
    @listen("hay_olas")
    def planificar(self):
        log(f"{ETAPAS['plan']} · {modelo('plan')} · olas {', '.join(f'{k} ({v})' for k, v in self.state.olas_pasan.items())}")
        supuestos_b = {o["id"]: o["supuestos"] for o in self.state.olas if self.state.olas_pasan.get(o["id"]) == "B"}
        if self.state.sin_llm:
            destino = self.root / "docs/tasks"
            destino.mkdir(parents=True, exist_ok=True)
            for f in (REF / "plan").iterdir():
                shutil.copy(f, destino / f.name)
            log("   (sin LLM: referencia/plan/)")
        else:
            olas_txt = "\n".join(
                f"- {o['id']} · {o['nombre']} · nota {o['nota']} · CA: {', '.join(self.state.cas.get(o['id'], []))}"
                + (f" · SUPUESTOS A REGISTRAR: {' | '.join(o['supuestos'])}" if o["id"] in supuestos_b else "")
                for o in self.state.olas if o["id"] in self.state.olas_pasan)
            errores: list[str] = []
            for intento in (1, 2):
                extra = "" if not errores else "\n\nTu paquete anterior no pasó la validación. Corrige esto:\n- " + "\n- ".join(errores)
                self.tarea(
                    "plan",
                    "Aplica la skill create-implementation-plan para estas olas aprobadas de la spec. Genera SOLO el paquete de "
                    "tareas (pasos 3 a 6): docs/tasks/task-package.yaml, docs/tasks/milestones.md y un archivo por tarea en "
                    "docs/tasks/. No crees AGENTS.md, README ni docs/architecture.md. Reglas para este ejercicio:\n"
                    "- planningWave: escalamiento-humano; un milestone por ola.\n"
                    "- En 'areas' de cada tarea pon el id de su ola (ola-1, ola-2).\n"
                    "- En 'Acceptance Criteria' escribe los CA de su ola con su ID (CA-01, …) tal como están en la spec.\n"
                    "- En 'Test Plan' indica si el CA se prueba con unitarias (Vitest) o con BDD (Gherkin) y el comando.\n"
                    "- Las olas con nota B: escribe en la tarea una línea 'Supuesto: …' con el supuesto completo.\n"
                    "- El código vive en demo-app/lib/agent.ts de qa-e2e (léelo para el Context).\n\n"
                    f"--- OLAS APROBADAS ---\n{olas_txt}\n\n--- SPEC ---\n{self.state.spec_texto}{extra}",
                    "Confirmación de los archivos escritos en docs/tasks/.")
                errores, _ = validar_paquete(self.root, self.state.olas_pasan, supuestos_b, self.state.cas)
                if not errores:
                    break
                log(f"   plan inválido (intento {intento}): {len(errores)} errores")
        errores, orden = validar_paquete(self.root, self.state.olas_pasan, supuestos_b, self.state.cas)
        self.state.plan_errores = errores
        self.state.tareas = [{k: t.get(k) for k in ("id", "title", "milestone", "areas", "blockedBy", "file")} for t in orden]
        if errores:
            log(f"   paquete inválido: {errores[:3]}")
        else:
            log(f"   paquete válido: {len(orden)} tareas → {', '.join(t['id'] for t in orden)}")
            self.pausa("Plan listo (qa-e2e/docs/tasks/)")

    @router(planificar)
    def compuerta_plan(self):
        return "plan_valido" if not self.state.plan_errores else "plan_invalido"

    @listen("plan_invalido")
    def abortar_plan(self):
        self.state.final = "ABORTADO · el paquete de create-implementation-plan no pasó la validación"
        cerrar(self)

    # 3 · Diseñador de pruebas ──────────────────────────────────────────
    @listen("plan_valido")
    def escribir_pruebas(self):
        log(f"{ETAPAS['pruebas']} · {modelo('pruebas')}")
        if self.state.sin_llm:
            shutil.copy(REF / "pruebas/escalamiento.test.ts", self.root / "demo-app/__tests__/escalamiento.test.ts")
            shutil.copy(REF / "pruebas/escalamiento.feature", self.root / "tests/features/escalamiento.feature")
            matriz = MatrizPruebas.model_validate_json((REF / "matriz.json").read_text())
            log("   (sin LLM: referencia/pruebas/)")
        else:
            tareas = "\n\n".join((self.root / t["file"]).read_text() for t in self.state.tareas)
            pasos = (self.root / "steps/asistente.steps.ts").read_text()
            ejemplo = "\n".join((self.root / "demo-app/__tests__/agent.test.ts").read_text().splitlines()[:25])
            r, _ = self.tarea(
                "pruebas",
                "Escribe las pruebas de estas tareas ANTES de que exista el código. Para cada CA decide la estrategia:\n"
                "- TDD (lógica pura de generateResponse): unitarias Vitest en demo-app/__tests__/escalamiento.test.ts, "
                "importando desde '../lib/agent' como en el ejemplo.\n"
                "- BDD (lo que el usuario ve en el chat): Scenario en tests/features/escalamiento.feature con el Background "
                "'Given que el usuario está en la página principal' y SOLO frases de los steps existentes, copiadas carácter "
                "por carácter.\n"
                "El nombre de cada test o Scenario empieza con el ID de su CA (por ejemplo 'CA-03 …'). Cubre todos los CA de "
                "las tareas. No toques el código de la app ni las pruebas existentes.\n\n"
                f"--- TAREAS ---\n{tareas}\n\n--- STEPS EXISTENTES ---\n{pasos}\n\n--- EJEMPLO DE UNITARIA ---\n{ejemplo}",
                "Un JSON MatrizPruebas: una fila por CA con estrategia (TDD o BDD) y archivo.", output_pydantic=MatrizPruebas)
            matriz = r.pydantic
        self.state.matriz = [f.model_dump() for f in matriz.filas]
        self._huella = huella(self.root)
        for f in matriz.filas:
            log(f"   {f.ca} → {f.estrategia} · {f.archivo}")

    @router(escribir_pruebas)
    def compuerta_rojo(self):
        log(f"{ETAPAS['ejecutor']} · {modelo('ejecutor')} · fase ROJO (antes del código)")
        codigos = self.correr(SUITES_ROJO, "Fase ROJO: las pruebas nuevas deberían fallar porque el código aún no existe.")
        res = self.resultados(SUITES_ROJO)
        cas = self.todos_los_cas()
        cob = cobertura(cas, [r.nombre for r in res])
        ver = veredicto_por_ca(cas, res)
        self.state.rojo = {"codigos": codigos, "por_ca": ver}
        sin = [ca for ca, t in cob.items() if not t]
        log(f"   exit {codigos} · por CA: " + ", ".join(f"{ca}={'✅' if v else '❌' if v is False else '—'}" for ca, v in ver.items()))
        if sin:
            self.state.alertas.append(f"CA sin prueba: {', '.join(sin)}")
            return "sin_cobertura"
        ya_pasan = [ca for ca, v in ver.items() if v]
        if ya_pasan:
            self.state.alertas.append(f"Pruebas que pasan sin código: {', '.join(ya_pasan)}")
            return "test_inutil"
        self.pausa("Rojo confirmado")
        return "rojo_confirmado"

    @listen("sin_cobertura")
    def abortar_cobertura(self):
        self.state.final = "ABORTADO · hay criterios de aceptación sin prueba"
        cerrar(self)

    @listen("test_inutil")
    def abortar_inutil(self):
        self.state.final = "ABORTADO · hay pruebas que pasan sin cambiar el código: no prueban su criterio"
        cerrar(self)

    # 4 + 5 · Desarrollador ↔ Ejecutor ────────────────────────────────────
    @listen("rojo_confirmado")
    def ciclo_desarrollo(self):
        tareas = "\n\n".join((self.root / t["file"]).read_text() for t in self.state.tareas)
        pruebas = "\n\n".join(f"--- {p} ---\n{(self.root / p).read_text()}" for p in
                              ("demo-app/__tests__/escalamiento.test.ts", "tests/features/escalamiento.feature") if (self.root / p).exists())
        falla = "\n".join(f"[{s}]\n{self.registro.ultima(s).salida}" for s in SUITES_ROJO)
        cas = self.todos_los_cas()
        for intento in range(1, self.state.max_reintentos + 2):
            log(f"{ETAPAS['dev']} · {modelo('dev')} · intento {intento}")
            if self.state.sin_llm:
                shutil.copy(REF / f"agent-intento-{min(intento, 2)}.ts", self.root / "demo-app/lib/agent.ts")
                log(f"   (sin LLM: agent-intento-{min(intento, 2)}.ts)")
            else:
                self.tarea(
                    "dev",
                    "Implementa estas tareas EN EL ORDEN DEL PLAN, cambiando solo demo-app/lib/agent.ts (léelo primero y "
                    "escribe el archivo completo). Respeta las reglas y los supuestos escritos en cada tarea. No rompas las "
                    "pruebas existentes.\n\n"
                    f"--- PLAN (en orden) ---\n{tareas}\n\n--- PRUEBAS QUE DEBEN PASAR ---\n{pruebas}\n\n--- ÚLTIMA FALLA ---\n{falla}",
                    "Qué cambiaste en agent.ts, en una o dos frases.")
            if huella(self.root) != self._huella:
                self.state.final = "ABORTADO · las pruebas cambiaron durante el desarrollo"
                cerrar(self)
                return
            log(f"{ETAPAS['ejecutor']} · {modelo('ejecutor')} · fase VERDE (unit + bdd + e2e)")
            codigos = self.correr(SUITES_VERDE, f"Intento {intento} de desarrollo: verifica los CA y la regresión.")
            ver = veredicto_por_ca(cas, self.resultados(SUITES_VERDE))
            falla = "\n\n".join(f"[{s}]\n{self.registro.ultima(s).salida}" for s, c in codigos.items() if c != 0)
            self.state.intentos.append({"intento": intento, "codigos": codigos, "por_ca": ver, "falla": falla})
            log(f"   exit {codigos} · " + ", ".join(f"{ca}={'✅' if v else '❌'}" for ca, v in ver.items()))
            if all(c == 0 for c in codigos.values()) and all(ver.values()):
                self.state.final = f"VERDE en el intento {intento}"
                break
            if intento <= self.state.max_reintentos:
                self.pausa(f"Intento {intento} en rojo: regresa a desarrollo")
        else:
            self.state.final = f"ROJO después de {self.state.max_reintentos} reintentos: lo revisa una persona"
        self.hacer_match()
        cerrar(self)

    def hacer_match(self):
        log(f"{ETAPAS['ejecutor']} · {modelo('ejecutor')} · match CA ↔ tarea ↔ cambio")
        if self.state.sin_llm:
            m = Match.model_validate_json((REF / "match.json").read_text())
        else:
            diff = diff_agent(self.root)
            tareas = "\n".join(f"{t['id']} · {t['title']} · {t['areas']}" for t in self.state.tareas)
            r, _ = self.tarea(
                "ejecutor",
                "Relaciona cada criterio de aceptación con su tarea del plan y con la parte del cambio en agent.ts que lo "
                "cubre (regla, condición o línea). No inventes: usa solo el diff y las tareas.\n\n"
                f"CA: {', '.join(self.todos_los_cas())}\n\n--- TAREAS ---\n{tareas}\n\n--- DIFF ---\n{diff}",
                "Un JSON Match con una fila por CA.", output_pydantic=Match, registro=self.registro)
            m = r.pydantic
        self.state.match = m.model_dump()


# ───────────────────────── salidas

def escribir_spec_review(st: Estado) -> None:
    OUT.mkdir(exist_ok=True)
    partes = [f"# Spec review · {Path(st.spec_path).name}\n",
              "| Ola | Nota (código) | Nota (LLM) | Decisión |", "|---|---|---|---|"]
    for o in st.olas:
        dec = "pasa" if o["nota"] == "A" else "pasa con supuestos (plan obligatorio)" if o["nota"] == "B" else "vuelve a diseño"
        partes.append(f"| {o['id']} · {o['nombre']} | **{o['nota']}** | {o['nota_llm']} | {dec} |")
    for o in st.olas:
        partes += [f"\n## {o['id']} · {o['nombre']} · {o['nota']}\n", *[f"- {r}" for r in o["razones"]]]
        if o["supuestos"]:
            partes += ["", "Supuestos (pendientes de aprobación):", *[f"- {s}" for s in o["supuestos"]]]
        if o["vacios"]:
            partes += ["", "Vacíos más graves:", *[f"{i}. {v}" for i, v in enumerate(o["vacios"], 1)]]
        partes += ["", "| Criterio | Estado | Evidencia | Corrección mínima |", "|---|---|---|---|"]
        partes += [f"| {c['id']} | {c['estado']} | {c['evidencia'] or '—'} | {c['correccion'] or ''} |" for c in o["criterios"]]
    (OUT / "spec-review.md").write_text("\n".join(partes) + "\n", encoding="utf-8")


def diff_agent(root: Path) -> str:
    return subprocess.run(["git", "diff", "--", "demo-app/lib/agent.ts"], cwd=root, capture_output=True, text=True).stdout


def diff_qa_e2e(root: Path) -> str:
    d = diff_agent(root)
    nuevos = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", *VIGILADOS, "docs"],
                            cwd=root, capture_output=True, text=True).stdout.split()
    return d + "".join(f"\n--- archivo nuevo: {n}\n" for n in nuevos) if (d or nuevos) else "(sin cambios)"


def resumen_falla(texto: str) -> str:
    claves = ("✘", "×", "FAIL", "Error", "Expected", "Received", "expected", "failed", "passed")
    lineas = [l for l in texto.splitlines() if any(k in l for k in claves)]
    return "\n".join(lineas[:30]) or texto[-1500:]


def cerrar(flow: QACrewFlow) -> None:
    st = flow.state
    OUT.mkdir(exist_ok=True)
    estr = {f["ca"]: f for f in st.matriz}
    match = {f["ca"]: f for f in (st.match or {}).get("filas", [])}
    ultimo = st.intentos[-1]["por_ca"] if st.intentos else {}

    def icono(v):
        return "✅" if v else "❌" if v is False else "—"

    filas = []
    for ola in st.olas_pasan:
        for ca in st.cas.get(ola, []):
            e, m = estr.get(ca, {}), match.get(ca, {})
            filas.append(f"| {ola} | {ca} | {e.get('estrategia', '—')} | `{e.get('archivo', '—')}` | {icono(st.rojo.get('por_ca', {}).get(ca))} "
                         f"| {icono(ultimo.get(ca))} | {m.get('tarea', '—')} | {m.get('cambio', '—')} |")
    intentos = "\n".join(f"| {i['intento']} | " + " | ".join("✅" if i['codigos'].get(s) == 0 else f"❌ ({i['codigos'].get(s)})" for s in SUITES_VERDE) + " |"
                         for i in st.intentos)
    fallas = "".join(f"### Falla del intento {i['intento']}\n\n```\n{resumen_falla(i['falla'])}\n```\n\n" for i in st.intentos if i.get("falla"))
    tok = "\n".join(f"| {ETAPAS[e]} | `{v['modelo']}` | {v['entrada']:,} | {v['salida']:,} |" for e, v in sorted(st.tokens.items(), key=lambda kv: list(ETAPAS).index(kv[0])))
    olas = "\n".join(f"| {o['id']} · {o['nombre']} | **{o['nota']}** | {o['nota_llm']} |" for o in st.olas)
    tareas = "\n".join(f"| {t['id']} | {t['title']} | {', '.join(t.get('areas') or [])} | {', '.join(t.get('blockedBy') or []) or '—'} |" for t in st.tareas)
    rep = (
        f"# QA crew · reporte\n\n- Spec: `{st.spec_path}`\n- Modo: {'sin LLM (referencia)' if st.sin_llm else 'con Claude'}\n"
        f"- Fecha: {datetime.now():%Y-%m-%d %H:%M}\n\n## Resultado: {st.final}\n\n"
        f"## 1 · Olas ({modelo('revisor')})\n\n| Ola | Nota del código | Nota del LLM |\n|---|---|---|\n{olas}\n\nDetalle en `out/spec-review.md`.\n\n"
        f"## 2 · Plan ({modelo('plan')})\n\n"
        + (f"| Tarea | Título | Ola | Bloqueada por |\n|---|---|---|---|\n{tareas}\n\nPaquete en `qa-e2e/docs/tasks/`.\n\n" if st.tareas else "")
        + ("Errores de validación:\n" + "\n".join(f"- {e}" for e in st.plan_errores) + "\n\n" if st.plan_errores else "")
        + f"## 3 a 5 · Matriz (pruebas: {modelo('pruebas')} · desarrollo: {modelo('dev')} · ejecución: {modelo('ejecutor')})\n\n"
        "| Ola | CA | Estrategia | Prueba | Rojo antes | Verde después | Tarea | Cambio que lo cubre |\n|---|---|---|---|---|---|---|---|\n"
        + ("\n".join(filas) or "| — |") + "\n\n"
        + (f"## Intentos de desarrollo\n\n| Intento | unit | bdd | e2e |\n|---|---|---|---|\n{intentos}\n\n{fallas}" if st.intentos else "")
        + (f"## Tokens por etapa\n\n| Etapa | Modelo | Entrada | Salida |\n|---|---|---|---|\n{tok}\n\n" if tok else "")
        + ("## Alertas\n\n" + "\n".join(f"- {a}" for a in st.alertas) + "\n\n" if st.alertas else "")
        + f"## Cambios en qa-e2e (revísalos tú; el crew no hace commit)\n\n```diff\n{diff_qa_e2e(flow.root)}\n```\n"
    )
    (OUT / "reporte.md").write_text(rep, encoding="utf-8")
    (OUT / "run.json").write_text(json.dumps(st.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"RESULTADO: {st.final} → out/reporte.md")


# ───────────────────────── CLI

def reset() -> None:
    root = qa_e2e_dir()
    subprocess.run(["git", "checkout", "--", "demo-app/lib/agent.ts", "tests", "steps", "demo-app/__tests__"], cwd=root, check=True)
    subprocess.run(["git", "clean", "-fdq", "--", "tests", "steps", "demo-app/__tests__", "docs"], cwd=root, check=True)
    shutil.rmtree(OUT, ignore_errors=True)
    log(f"reset listo: {root} limpio y out/ borrado")


def preflight(sin_llm: bool) -> list[str]:
    root, errores = qa_e2e_dir(), []
    if not (root / "node_modules").exists() or not (root / "demo-app/node_modules").exists():
        errores.append(f"Faltan dependencias en {root}: npm install ahí y en demo-app/")
    url = os.environ.get("BASE_URL", "http://localhost:3000")
    try:
        urllib.request.urlopen(url, timeout=5)
    except Exception:
        errores.append(f"La demo-app no responde en {url}: cd {root}/demo-app && npm run dev")
    if not sin_llm and not os.environ.get("ANTHROPIC_API_KEY"):
        errores.append("Falta ANTHROPIC_API_KEY (export ANTHROPIC_API_KEY=sk-ant-...) o usa --sin-llm")
    sucio = subprocess.run(["git", "status", "--porcelain", "--", "demo-app/lib/agent.ts", *VIGILADOS, "docs"],
                           cwd=root, capture_output=True, text=True).stdout.strip()
    if sucio:
        errores.append(f"qa-e2e tiene cambios de una corrida anterior:\n{sucio}\n  → uv run crew --reset")
    return errores


def cli() -> None:
    cargar_env()
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
    ap = argparse.ArgumentParser(prog="crew", description="QA crew · E8 bonus")
    ap.add_argument("--spec", help="ruta a la spec, p. ej. specs/escalamiento.md")
    ap.add_argument("--sin-llm", action="store_true", help="plan B: usa referencia/ en lugar de llamar a los modelos")
    ap.add_argument("--pausar", action="store_true", help="se detiene entre etapas hasta que presiones Enter")
    ap.add_argument("--max-reintentos", type=int, default=2)
    ap.add_argument("--reset", action="store_true", help="deshace los cambios en qa-e2e y borra out/")
    a = ap.parse_args()
    if a.reset:
        reset()
        return
    if not a.spec:
        ap.error("falta --spec")
    spec = (AQUI / a.spec).resolve() if not Path(a.spec).is_absolute() else Path(a.spec)
    errores = preflight(a.sin_llm)
    if errores:
        for e in errores:
            print(f"✗ {e}", file=sys.stderr)
        sys.exit(2)
    if not a.sin_llm:
        log("modelos: " + " · ".join(f"{ETAPAS[e].split(' · ')[1]}={modelo(e).split('/')[-1]}" for e in ETAPAS))
    flow = QACrewFlow()
    flow.kickoff(inputs={
        "spec_path": str(spec.relative_to(AQUI)) if spec.is_relative_to(AQUI) else str(spec),
        "spec_texto": spec.read_text(encoding="utf-8"),
        "sin_llm": a.sin_llm, "pausar": a.pausar, "max_reintentos": a.max_reintentos,
    })
    final = flow.state.final
    sys.exit(0 if final.startswith("VERDE") else 3 if final.startswith("DETENIDO") else 1)


if __name__ == "__main__":
    cli()
