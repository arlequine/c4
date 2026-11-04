"""Herramientas con guardrails: cada agente solo lee y escribe donde le toca,
y solo puede correr las suites de una lista blanca.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

SUITES: dict[str, list[str]] = {
    "bdd": ["npm", "run", "test:bdd"],
    "e2e": ["npx", "playwright", "test", "--project=chromium"],
    "unit": ["npm", "--prefix", "demo-app", "run", "test:unit"],
}


@dataclass
class Ejecucion:
    suite: str
    exit_code: int
    salida: str  # últimas líneas


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


def correr_suite(root: Path, suite: str, registro: Registro, timeout: int = 300) -> Ejecucion:
    if suite not in SUITES:
        raise PermissionError(f"Suite no permitida: {suite}. Permitidas: {', '.join(SUITES)}")
    try:
        env = {**os.environ, "FORCE_COLOR": "0", "CI": os.environ.get("CI", "")}
        proc = subprocess.run(SUITES[suite], cwd=root, capture_output=True, text=True, timeout=timeout, env=env)
        code, out = proc.returncode, (proc.stdout + proc.stderr)
    except subprocess.TimeoutExpired as e:
        code, out = 124, f"Timeout después de {timeout}s\n{e.stdout or ''}"
    out = re.sub(r"\x1b\[[0-9;]*m", "", out)
    lineas = [l for l in out.splitlines() if l.strip()]
    ej = Ejecucion(suite, code, "\n".join(lineas[-60:]))
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
        "Suites: bdd (npm run test:bdd), e2e (playwright chromium), unit (vitest de demo-app)."
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
        return f"suite={ej.suite} exit_code={ej.exit_code}\n{ej.salida}"
