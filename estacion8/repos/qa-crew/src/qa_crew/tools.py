"""Herramientas con guardrails: cada agente solo lee y escribe donde le toca,
y solo puede correr las suites de una lista blanca.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from .gate import ResultadoTest

SUITES: dict[str, dict] = {
    # cwd relativo a qa-e2e/; {json} se reemplaza por la ruta del reporte JSON
    "unit": {"cwd": "demo-app", "cmd": ["npx", "vitest", "run", "--reporter=default", "--reporter=json", "--outputFile.json={json}"]},
    "bdd": {"cwd": ".", "cmd": ["npm", "run", "test:bdd", "--", "--reporter=list,json"]},
    "e2e": {"cwd": ".", "cmd": ["npx", "playwright", "test", "--project=chromium", "--reporter=list,json"]},
}


@dataclass
class Ejecucion:
    suite: str
    exit_code: int
    salida: str  # últimas líneas
    resultados: list[ResultadoTest] = field(default_factory=list)


@dataclass
class Registro:
    """Lo que de verdad pasó. El flow decide con esto, no con el texto del agente."""

    ejecuciones: list[Ejecucion] = field(default_factory=list)

    def ultima(self, suite: str) -> Ejecucion | None:
        for e in reversed(self.ejecuciones):
            if e.suite == suite:
                return e
        return None


def _dentro(root: Path, ruta: str) -> Path:
    p = (root / ruta).resolve()
    if root.resolve() not in (p, *p.parents):
        raise PermissionError(f"Ruta fuera del proyecto: {ruta}")
    return p


def _leer_vitest(path: Path) -> list[ResultadoTest]:
    d = json.loads(path.read_text())
    return [
        ResultadoTest(nombre=a.get("fullName") or a.get("title", ""), ok=a.get("status") == "passed", suite="unit")
        for f in d.get("testResults", []) for a in f.get("assertionResults", [])
    ]


def _leer_playwright(path: Path, suite: str) -> list[ResultadoTest]:
    d = json.loads(path.read_text())
    out: list[ResultadoTest] = []

    def walk(s: dict, ruta: list[str]) -> None:
        for sp in s.get("specs", []):
            out.append(ResultadoTest(nombre=" > ".join([*ruta, sp.get("title", "")]), ok=bool(sp.get("ok")), suite=suite))
        for c in s.get("suites", []):
            walk(c, [*ruta, c.get("title", "")])

    for s in d.get("suites", []):
        walk(s, [s.get("title", "")])
    return out


def correr_suite(root: Path, suite: str, registro: Registro, timeout: int = 300) -> Ejecucion:
    if suite not in SUITES:
        raise PermissionError(f"Suite no permitida: {suite}. Permitidas: {', '.join(SUITES)}")
    conf = SUITES[suite]
    with tempfile.TemporaryDirectory() as tmp:
        reporte = Path(tmp) / f"{suite}.json"
        cmd = [c.replace("{json}", str(reporte)) for c in conf["cmd"]]
        env = {**os.environ, "FORCE_COLOR": "0", "PLAYWRIGHT_JSON_OUTPUT_NAME": str(reporte)}
        try:
            proc = subprocess.run(cmd, cwd=root / conf["cwd"], capture_output=True, text=True, timeout=timeout, env=env)
            code, out = proc.returncode, (proc.stdout + proc.stderr)
        except subprocess.TimeoutExpired as e:
            code, out = 124, f"Timeout después de {timeout}s\n{e.stdout or ''}"
        resultados: list[ResultadoTest] = []
        if reporte.exists():
            try:
                resultados = _leer_vitest(reporte) if suite == "unit" else _leer_playwright(reporte, suite)
            except (ValueError, KeyError):
                pass
    out = re.sub(r"\x1b\[[0-9;]*m", "", out)
    lineas = [l for l in out.splitlines() if l.strip() and not l.startswith("JSON report written")]
    ej = Ejecucion(suite, code, "\n".join(lineas[-60:]), resultados)
    registro.ejecuciones.append(ej)
    return ej


class _LeerArgs(BaseModel):
    ruta: str = Field(description="Ruta relativa a qa-e2e/, por ejemplo demo-app/lib/agent.ts")


class LeerArchivo(BaseTool):
    name: str = "leer_archivo"
    description: str = "Lee un archivo de texto del proyecto qa-e2e. Si la ruta es una carpeta, lista su contenido."
    args_schema: type[BaseModel] = _LeerArgs
    _root: Path = PrivateAttr()

    def __init__(self, root: Path, **kw):
        super().__init__(**kw)
        self._root = root

    def _run(self, ruta: str) -> str:
        try:
            p = _dentro(self._root, ruta)
        except PermissionError as e:
            return f"ERROR: {e}"
        if any(part in ("node_modules", ".next", ".git") for part in p.parts):
            return "ERROR: carpeta no permitida"
        if p.is_dir():
            return "\n".join(sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir()))
        if not p.exists():
            return f"ERROR: no existe {ruta}"
        return p.read_text(encoding="utf-8")[:20000]


class _EscribirArgs(BaseModel):
    ruta: str = Field(description="Ruta relativa a qa-e2e/")
    contenido: str = Field(description="Contenido completo del archivo")


class EscribirArchivo(BaseTool):
    name: str = "escribir_archivo"
    description: str = "Escribe un archivo completo en qa-e2e. Solo funciona en las rutas permitidas para tu rol."
    args_schema: type[BaseModel] = _EscribirArgs
    _root: Path = PrivateAttr()
    _permitidas: tuple[str, ...] = PrivateAttr()
    _protegidas: tuple[str, ...] = PrivateAttr()
    _escritos: list[str] = PrivateAttr(default_factory=list)

    def __init__(self, root: Path, permitidas: tuple[str, ...], protegidas: tuple[str, ...] = (), **kw):
        super().__init__(**kw)
        self._root, self._permitidas, self._protegidas = root, permitidas, protegidas
        self._escritos = []
        self.description += f" Rutas permitidas: {', '.join(permitidas)}."

    @property
    def escritos(self) -> list[str]:
        return list(self._escritos)

    def _run(self, ruta: str, contenido: str) -> str:
        rel = ruta.strip().removeprefix("./")
        if any(fnmatch.fnmatch(rel, g) for g in self._protegidas) or not any(fnmatch.fnmatch(rel, g) for g in self._permitidas):
            return f"ERROR: tu rol no puede escribir {rel}. Permitidas: {', '.join(self._permitidas)}"
        try:
            p = _dentro(self._root, rel)
        except PermissionError as e:
            return f"ERROR: {e}"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
        if rel not in self._escritos:
            self._escritos.append(rel)
        return f"OK: escrito {rel} ({len(contenido)} caracteres)"


class _CorrerArgs(BaseModel):
    suite: str = Field(description="Una de: bdd, e2e, unit")


class CorrerPruebas(BaseTool):
    name: str = "correr_pruebas"
    description: str = (
        "Corre una suite de pruebas de qa-e2e y devuelve el exit code y las últimas líneas. "
        "Suites: unit (Vitest de demo-app), bdd (npm run test:bdd), e2e (Playwright en Chromium)."
    )
    args_schema: type[BaseModel] = _CorrerArgs
    _root: Path = PrivateAttr()
    _registro: Registro = PrivateAttr()

    def __init__(self, root: Path, registro: Registro, **kw):
        super().__init__(**kw)
        self._root, self._registro = root, registro

    def _run(self, suite: str) -> str:
        try:
            ej = correr_suite(self._root, suite.strip().lower(), self._registro)
        except PermissionError as e:
            return f"ERROR: {e}"
        fallas = [r.nombre for r in ej.resultados if not r.ok]
        detalle = ("\nPruebas que fallaron:\n- " + "\n- ".join(fallas)) if fallas else ""
        return f"suite={ej.suite} exit_code={ej.exit_code} pruebas={len(ej.resultados)} fallaron={len(fallas)}{detalle}\n{ej.salida}"
