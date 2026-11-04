"""QA crew · E8 bonus.

Cuatro agentes llevan una spec hasta un E2E en verde sobre qa-e2e:
  1. Revisor de spec   (skill evaluate-spec de la E6)  → la nota la recalcula el código
  2. QA                (skill qa-testing de la E8)     → .feature que debe fallar primero
  3. Desarrollo        (solo demo-app/lib/agent.ts)    → no puede tocar los tests
  4. Ejecutor E2E      (lista blanca de suites)        → el exit code decide, máx. N reintentos

Uso:
  uv run crew --spec specs/spec-lista.md            # con Claude (ANTHROPIC_API_KEY)
  uv run crew --spec specs/spec-lista.md --sin-llm  # plan B: respuestas de referencia/, pruebas reales
  uv run crew --reset                               # deja qa-e2e y out/ como estaban
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

from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, router, start

from .gate import RevisionSpec, calcular_nota, pasa
from .tools import CorrerPruebas, EscribirArchivo, LeerArchivo, Registro, correr_suite

AQUI = Path(__file__).resolve().parents[2]  # qa-crew/
REF = AQUI / "referencia"
OUT = AQUI / "out"
SKILLS = AQUI / "skills"

QA_PERMITIDAS = ("tests/features/*.feature", "steps/*.steps.ts")
QA_PROTEGIDAS = ("tests/features/asistente.feature", "steps/asistente.steps.ts")
DEV_PERMITIDAS = ("demo-app/lib/agent.ts",)
VIGILADOS = ("tests/features", "steps")


def log(msg: str) -> None:
    print(f"[qa-crew {datetime.now():%H:%M:%S}] {msg}", flush=True)


def cargar_env() -> None:
    """Lee qa-crew/.env si existe (sin pisar variables ya exportadas)."""
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


# ───────────────────────── estado del flow

class Estado(BaseModel):
    spec_path: str = ""
    spec_texto: str = ""
    sin_llm: bool = False
    max_reintentos: int = 2
    revision: dict | None = None
    nota: str = ""
    nota_llm: str = ""
    razones: list[str] = []
    archivos_tests: list[str] = []
    huella_tests: str = ""
    rojo_exit: int | None = None
    intentos: list[dict] = []
    final: str = ""
    alertas: list[str] = []


# ───────────────────────── agentes (solo en modo con LLM)

def _llm():
    from crewai import LLM

    return LLM(model=os.environ.get("QA_MODEL", "anthropic/claude-sonnet-5-5"), temperature=0.1)


def _skill(nombre: str):
    from crewai.skills import activate_skill, discover_skills

    return [activate_skill(s) for s in discover_skills(SKILLS) if s.frontmatter.name == nombre]


def _correr_tarea(agente, descripcion: str, esperado: str, output_pydantic=None):
    from crewai import Crew, Task

    t = Task(description=descripcion, expected_output=esperado, agent=agente, output_pydantic=output_pydantic)
    r = Crew(agents=[agente], tasks=[t], verbose=True).kickoff()
    return r


def agente_revisor(root: Path):
    from crewai import Agent

    return Agent(
        role="Revisor de spec",
        goal="Decidir con evidencia si la spec está lista para implementarse, aplicando la skill evaluate-spec.",
        backstory="Revisas specs antes de que el equipo planifique. No apruebas nada sin evidencia citada.",
        llm=_llm(), skills=_skill("evaluate-spec"), tools=[LeerArchivo(root)], allow_delegation=False, max_iter=8,
    )


def agente_qa(root: Path):
    from crewai import Agent

    return Agent(
        role="QA engineer",
        goal="Convertir los criterios de aceptación en escenarios Gherkin ejecutables que fallen antes del cambio.",
        backstory="Sigues las convenciones de la skill qa-testing. Reutilizas los steps existentes en lugar de inventar.",
        llm=_llm(), skills=_skill("qa-testing"),
        tools=[LeerArchivo(root), EscribirArchivo(root, QA_PERMITIDAS, QA_PROTEGIDAS)], allow_delegation=False, max_iter=10,
    )


def agente_dev(root: Path):
    from crewai import Agent

    return Agent(
        role="Desarrollador",
        goal="Hacer pasar los escenarios cambiando solo demo-app/lib/agent.ts, sin romper lo que ya funciona.",
        backstory="Trabajas con TDD: los tests son la spec. Nunca modificas un test para que pase.",
        llm=_llm(), tools=[LeerArchivo(root), EscribirArchivo(root, DEV_PERMITIDAS)], allow_delegation=False, max_iter=10,
    )


def agente_ejecutor(root: Path, registro: Registro):
    from crewai import Agent

    return Agent(
        role="Ejecutor E2E",
        goal="Correr las suites pedidas y resumir con precisión qué falló.",
        backstory="Eres el último filtro. Reportas hechos: escenario, esperado y obtenido. No propones código.",
        llm=_llm(), tools=[CorrerPruebas(root, registro)], allow_delegation=False, max_iter=6,
    )


# ───────────────────────── flow

class QACrewFlow(Flow[Estado]):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.root = qa_e2e_dir()
        self.registro = Registro()

    # 1 · Revisor de spec ────────────────────────────────────────────
    @start()
    def revisar_spec(self):
        log(f"1/4 Revisor de spec · {self.state.spec_path}")
        if self.state.sin_llm:
            nombre = Path(self.state.spec_path).stem
            rev = RevisionSpec.model_validate_json((REF / f"revision-{nombre}.json").read_text())
            log(f"   (sin LLM: revisión de referencia/revision-{nombre}.json)")
        else:
            r = _correr_tarea(
                agente_revisor(self.root),
                "Evalúa esta spec con la skill evaluate-spec. Es una sola ola. Evalúa los 14 criterios "
                "(P1–P6, T1–T4, D1–D4) como Cumple, Parcial, Falta o N/A, citando la sección de la spec. "
                "Si un crítico es Parcial y se cierra con un supuesto, escríbelo en 'supuesto'. "
                "Puedes leer qa-e2e para verificar el diseño (por ejemplo demo-app/lib/agent.ts). "
                "No escribas archivos: devuelve solo el JSON.\n\n--- SPEC ---\n" + self.state.spec_texto,
                "Un JSON RevisionSpec con los 14 criterios, nota_llm, vacios_graves y resumen.",
                output_pydantic=RevisionSpec,
            )
            rev = r.pydantic
        nota, razones = calcular_nota(rev.criterios)
        self.state.revision, self.state.nota, self.state.nota_llm, self.state.razones = rev.model_dump(), nota, rev.nota_llm, razones
        if nota != rev.nota_llm:
            self.state.alertas.append(f"El LLM puso {rev.nota_llm}, el código calcula {nota}. Manda el código.")
        escribir_spec_review(self.state)
        log(f"   nota del código: {nota} · nota del LLM: {rev.nota_llm} → out/spec-review.md")

    @router(revisar_spec)
    def compuerta_spec(self):
        return "spec_lista" if pasa(self.state.nota) else "spec_no_lista"

    @listen("spec_no_lista")
    def detener(self):
        self.state.final = f"DETENIDO · la spec tiene nota {self.state.nota}: sin spec lista no se codea"
        cerrar(self)

    # 2 · QA escribe los tests ─────────────────────────────────────────
    @listen("spec_lista")
    def escribir_tests(self):
        log("2/4 QA · escribiendo escenarios")
        if self.state.sin_llm:
            destino = self.root / "tests/features/escalamiento.feature"
            shutil.copy(REF / "escalamiento.feature", destino)
            escritos = ["tests/features/escalamiento.feature"]
        else:
            ag = agente_qa(self.root)
            pasos = (self.root / "steps/asistente.steps.ts").read_text()
            _correr_tarea(
                ag,
                "Escribe tests/features/escalamiento.feature con un Scenario por cada criterio CA-01 a CA-03 de la spec "
                "(CA-04 es la regresión, no lo escribas). Usa el Background 'Given que el usuario está en la página principal' "
                "y SOLO frases de steps que ya existen, copiadas carácter por carácter (con acentos). No toques código de la app.\n\n"
                f"--- STEPS EXISTENTES (steps/asistente.steps.ts) ---\n{pasos}\n\n--- SPEC ---\n{self.state.spec_texto}",
                "Confirmación de los archivos escritos.",
            )
            escritos = next(t for t in ag.tools if isinstance(t, EscribirArchivo)).escritos
        self.state.archivos_tests = escritos
        self.state.huella_tests = huella(self.root)
        log(f"   archivos: {', '.join(escritos) or '(ninguno)'}")

    @router(escribir_tests)
    def compuerta_rojo(self):
        if not self.state.archivos_tests:
            return "sin_tests"
        log("4/4 Ejecutor · fase ROJO (antes del código)")
        ej = self.ejecutar(["bdd"], "Fase ROJO: los escenarios nuevos deberían fallar porque el código aún no existe.")
        self.state.rojo_exit = ej["bdd"]
        log(f"   bdd exit={ej['bdd']} ({'ROJO, como se esperaba' if ej['bdd'] else 'VERDE: el test no prueba nada'})")
        return "rojo_confirmado" if ej["bdd"] != 0 else "test_inutil"

    @listen("sin_tests")
    def abortar_sin_tests(self):
        self.state.final = "ABORTADO · QA no escribió ningún test"
        cerrar(self)

    @listen("test_inutil")
    def abortar_inutil(self):
        self.state.final = "ABORTADO · los tests nuevos pasan sin cambiar el código: no prueban la feature"
        cerrar(self)

    # 3 + 4 · Desarrollo ↔ Ejecutor ────────────────────────────────────
    @listen("rojo_confirmado")
    def ciclo_desarrollo(self):
        feature = "\n".join((self.root / f).read_text() for f in self.state.archivos_tests)
        falla = self.registro.ultima("bdd").salida
        for intento in range(1, self.state.max_reintentos + 2):
            log(f"3/4 Desarrollo · intento {intento}")
            if self.state.sin_llm:
                ref = REF / f"agent-intento-{min(intento, 2)}.ts"
                shutil.copy(ref, self.root / "demo-app/lib/agent.ts")
                log(f"   (sin LLM: {ref.name})")
            else:
                _correr_tarea(
                    agente_dev(self.root),
                    "Haz que pasen los escenarios cambiando SOLO demo-app/lib/agent.ts (léelo primero y escribe el archivo completo). "
                    "Respeta las reglas de negocio de la spec. No rompas los escenarios ni los unitarios existentes.\n\n"
                    f"--- SPEC ---\n{self.state.spec_texto}\n\n--- ESCENARIOS ---\n{feature}\n\n--- ÚLTIMA FALLA ---\n{falla}",
                    "Confirmación de que escribiste demo-app/lib/agent.ts y qué cambiaste en una frase.",
                )
            if huella(self.root) != self.state.huella_tests:
                self.state.final = "ABORTADO · alguien modificó los tests durante el desarrollo"
                cerrar(self)
                return
            log("4/4 Ejecutor · fase VERDE (bdd + e2e + unit)")
            ej = self.ejecutar(["bdd", "e2e", "unit"], f"Intento {intento} de desarrollo: verifica la feature y la regresión (CA-04).")
            falla = "\n\n".join(f"[{s}]\n{self.registro.ultima(s).salida}" for s, v in ej.items() if v != 0)
            self.state.intentos.append({"intento": intento, **ej, "falla": falla})
            log(f"   {ej}")
            if all(v == 0 for v in ej.values()):
                self.state.final = f"VERDE en el intento {intento}"
                break
        else:
            self.state.final = f"ROJO después de {self.state.max_reintentos} reintentos: lo revisa un humano"
        cerrar(self)

    # utilidades ────────────────────────────────────────────────────────
    def ejecutar(self, suites: list[str], contexto: str) -> dict[str, int]:
        """El agente corre las suites; el veredicto sale del registro, no de su texto."""
        inicio = len(self.registro.ejecuciones)
        if not self.state.sin_llm:
            _correr_tarea(
                agente_ejecutor(self.root, self.registro),
                f"{contexto}\nCorre, en este orden, las suites: {', '.join(suites)}. "
                "Después resume en máximo 10 líneas qué escenarios fallaron, con lo esperado y lo obtenido.",
                "Resumen de fallas o 'todo en verde'.",
            )
        corridas = {e.suite: e.exit_code for e in self.registro.ejecuciones[inicio:]}
        for s in suites:
            if s not in corridas:
                if not self.state.sin_llm:
                    self.state.alertas.append(f"El ejecutor no corrió '{s}'; lo corrió el flow.")
                corridas[s] = correr_suite(self.root, s, self.registro).exit_code
        return {s: corridas[s] for s in suites}


# ───────────────────────── salidas

def escribir_spec_review(st: Estado) -> None:
    OUT.mkdir(exist_ok=True)
    rev = st.revision or {}
    filas = "\n".join(
        f"| {c['id']} | {c['estado']} | {c['evidencia'] or '—'} | {c['correccion'] or ''} |" for c in rev.get("criterios", [])
    )
    vacios = "\n".join(f"{i}. {v}" for i, v in enumerate(rev.get("vacios_graves", []), 1)) or "Ninguno."
    (OUT / "spec-review.md").write_text(
        f"# Spec review · {Path(st.spec_path).name}\n\n"
        f"**Nota (calculada por el código): {st.nota}** · nota que propuso el LLM: {st.nota_llm}\n\n"
        + "\n".join(f"- {r}" for r in st.razones)
        + f"\n\n{rev.get('resumen', '')}\n\n| Criterio | Estado | Evidencia | Corrección mínima |\n|---|---|---|---|\n{filas}\n\n"
        f"## Vacíos más graves\n\n{vacios}\n",
        encoding="utf-8",
    )


def resumen_falla(texto: str) -> str:
    """Las líneas que dicen qué escenario falló y por qué."""
    claves = ("✘", "Error", "Expected", "Received", "expect(", "failed", "passed")
    lineas = [l for l in texto.splitlines() if any(k in l for k in claves)]
    return "\n".join(lineas[:25]) or texto[-1500:]


def diff_qa_e2e(root: Path) -> str:
    d = subprocess.run(["git", "diff", "--", "demo-app/lib/agent.ts"], cwd=root, capture_output=True, text=True).stdout
    nuevos = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *VIGILADOS], cwd=root, capture_output=True, text=True
    ).stdout.split()
    for n in nuevos:
        d += f"\n--- archivo nuevo: {n}\n" + (root / n).read_text()
    return d or "(sin cambios)"


def cerrar(flow: QACrewFlow) -> None:
    st = flow.state
    OUT.mkdir(exist_ok=True)
    intentos = "\n".join(
        f"| {i['intento']} | " + " | ".join(("✅" if i.get(s) == 0 else f"❌ ({i.get(s)})") for s in ("bdd", "e2e", "unit")) + " |"
        for i in st.intentos
    )
    rep = (
        f"# QA crew · reporte\n\n- Spec: `{st.spec_path}`\n- Modo: {'sin LLM (referencia)' if st.sin_llm else os.environ.get('QA_MODEL', 'anthropic/claude-sonnet-5-5')}\n"
        f"- Fecha: {datetime.now():%Y-%m-%d %H:%M}\n\n## Resultado: {st.final}\n\n"
        f"## 1 · Revisor de spec\n\nNota del código: **{st.nota}** · nota del LLM: {st.nota_llm}. Detalle en `out/spec-review.md`.\n\n"
        f"## 2 · QA\n\nArchivos: {', '.join(st.archivos_tests) or '—'}\n\n"
        f"Fase rojo (`npm run test:bdd` antes del código): exit {st.rojo_exit if st.rojo_exit is not None else '—'}\n\n"
        f"## 3 + 4 · Desarrollo ↔ Ejecutor\n\n| Intento | bdd | e2e | unit |\n|---|---|---|---|\n{intentos or '| — | | | |'}\n\n"
        + "".join(
            f"### Falla del intento {i['intento']}\n\n```\n{resumen_falla(i['falla'])}\n```\n\n" for i in st.intentos if i.get("falla")
        )
        + ("## Alertas\n\n" + "\n".join(f"- {a}" for a in st.alertas) + "\n\n" if st.alertas else "")
        + f"## Diff en qa-e2e (revísalo tú; el crew no hace commit)\n\n```diff\n{diff_qa_e2e(flow.root)}\n```\n"
    )
    (OUT / "reporte.md").write_text(rep, encoding="utf-8")
    (OUT / "run.json").write_text(json.dumps(st.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"RESULTADO: {st.final} → out/reporte.md")


# ───────────────────────── CLI

def reset() -> None:
    root = qa_e2e_dir()
    subprocess.run(["git", "checkout", "--", "demo-app/lib/agent.ts", "tests", "steps"], cwd=root, check=True)
    subprocess.run(["git", "clean", "-fdq", "--", "tests", "steps"], cwd=root, check=True)
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
    sucio = subprocess.run(
        ["git", "status", "--porcelain", "--", "demo-app/lib/agent.ts", *VIGILADOS], cwd=root, capture_output=True, text=True
    ).stdout.strip()
    if sucio:
        errores.append(f"qa-e2e tiene cambios de una corrida anterior:\n{sucio}\n  → uv run crew --reset")
    return errores


def cli() -> None:
    cargar_env()
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
    ap = argparse.ArgumentParser(prog="crew", description="QA crew · E8 bonus")
    ap.add_argument("--spec", help="ruta a la spec, p. ej. specs/spec-lista.md")
    ap.add_argument("--sin-llm", action="store_true", help="plan B: usa referencia/ en lugar de llamar al LLM")
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
    flow = QACrewFlow()
    flow.kickoff(inputs={
        "spec_path": str(spec.relative_to(AQUI)) if spec.is_relative_to(AQUI) else str(spec),
        "spec_texto": spec.read_text(encoding="utf-8"),
        "sin_llm": a.sin_llm,
        "max_reintentos": a.max_reintentos,
    })
    sys.exit(0 if flow.state.final.startswith("VERDE") else 3 if flow.state.final.startswith("DETENIDO") else 1)


if __name__ == "__main__":
    cli()
