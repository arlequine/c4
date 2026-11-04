"""Compuertas que deciden por código, no por el LLM.

1. Nota por ola (skill evaluate-spec, E6):
     A  todos los críticos cumplen con evidencia
     B  ningún crítico falta; los parciales críticos tienen un supuesto escrito
     C  falta al menos un crítico, pero el alcance existe
     D  falta el alcance o no hay aceptación observable
   Un crítico "Parcial" sin supuesto cuenta como "Falta"; "Cumple" sin evidencia, también.
   Pasan a planificación las olas A y B (las B, solo si el plan registra sus supuestos).
2. Cobertura: cada CA de las olas que pasan tiene al menos una prueba con su ID en el nombre.
3. Veredicto por CA: sale de los reportes JSON de Vitest y Playwright.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

Estado = Literal["Cumple", "Parcial", "Falta", "N/A"]
Nota = Literal["A", "B", "C", "D"]

CRITICOS = ("P1", "P2", "P3", "P4", "T1", "T2", "D1")
TODOS = ("P1", "P2", "P3", "P4", "P5", "P6", "T1", "T2", "T3", "T4", "D1", "D2", "D3", "D4")
CA_RE = re.compile(r"\bCA-\d{2}\b")


class Criterio(BaseModel):
    id: str = Field(description="P1..P6, T1..T4 o D1..D4")
    estado: Estado
    evidencia: str = Field(default="", description="Sección o línea de la spec que lo respalda; vacío si no hay")
    correccion: str = Field(default="", description="Corrección mínima si no cumple")
    supuesto: str = Field(default="", description="Supuesto escrito que cierra un Parcial, si existe")


class Ola(BaseModel):
    id: str = Field(description="ola-1, ola-2, …")
    nombre: str
    criterios: list[Criterio]
    nota_llm: Nota = Field(description="La nota que tú le pondrías a esta ola según la skill")
    vacios_graves: list[str] = Field(default_factory=list)


class RevisionSpec(BaseModel):
    olas: list[Ola]
    resumen: str = ""


def calcular_nota(criterios: list[Criterio]) -> tuple[Nota, list[str]]:
    por_id = {c.id.strip().upper(): c for c in criterios}
    razones: list[str] = []

    def efectivo(cid: str) -> str:
        c = por_id.get(cid)
        if c is None:
            razones.append(f"{cid}: no evaluado → cuenta como Falta")
            return "Falta"
        if c.estado == "Parcial" and not c.supuesto.strip():
            razones.append(f"{cid}: Parcial sin supuesto escrito → cuenta como Falta")
            return "Falta"
        if c.estado in ("Cumple", "Parcial") and not c.evidencia.strip():
            razones.append(f"{cid}: {c.estado} sin evidencia citada → cuenta como Falta")
            return "Falta"
        return c.estado

    estados = {cid: efectivo(cid) for cid in CRITICOS}
    if estados["P2"] == "Falta" or estados["T1"] == "Falta":
        razones.append("Falta el alcance (P2) o la aceptación observable (T1) → D")
        return "D", razones
    faltan = [c for c, e in estados.items() if e == "Falta"]
    if faltan:
        razones.append(f"Críticos que faltan: {', '.join(faltan)} → C")
        return "C", razones
    parciales = [c for c, e in estados.items() if e == "Parcial"]
    if parciales:
        razones.append(f"Críticos parciales cerrados con supuesto: {', '.join(parciales)} → B")
        return "B", razones
    razones.append("Todos los críticos cumplen con evidencia → A")
    return "A", razones


def supuestos(ola: Ola) -> list[str]:
    return [c.supuesto.strip() for c in ola.criterios if c.estado == "Parcial" and c.supuesto.strip()]


def pasa(nota: Nota) -> bool:
    return nota in ("A", "B")


# ───────────── CA por ola, leídos de la spec (no del LLM)

def cas_por_ola(spec: str) -> dict[str, list[str]]:
    """{'ola-1': ['CA-01', …], …} según las secciones '## Ola N' de la spec."""
    out: dict[str, list[str]] = {}
    partes = re.split(r"^## Ola (\d+)\b", spec, flags=re.M)
    for i in range(1, len(partes), 2):
        ids: list[str] = []
        for m in CA_RE.findall(partes[i + 1]):
            if m not in ids:
                ids.append(m)
        out[f"ola-{partes[i]}"] = ids
    return out


# ───────────── resultados por CA

class ResultadoTest(BaseModel):
    nombre: str
    ok: bool
    suite: str


def cobertura(cas: list[str], nombres_tests: list[str]) -> dict[str, list[str]]:
    return {ca: [n for n in nombres_tests if ca in n] for ca in cas}


def veredicto_por_ca(cas: list[str], resultados: list[ResultadoTest]) -> dict[str, bool | None]:
    """True si todas las pruebas con ese CA pasan; False si alguna falla; None si no hay pruebas."""
    out: dict[str, bool | None] = {}
    for ca in cas:
        r = [x.ok for x in resultados if ca in x.nombre]
        out[ca] = None if not r else all(r)
    return out
