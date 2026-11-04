"""Compuerta de la spec: la nota la calcula el código, no el LLM.

Implementa la tabla "Nota por ola" de la skill evaluate-spec (E6):
  A  todos los críticos cumplen
  B  ningún crítico falta; los parciales críticos tienen un supuesto escrito
  C  falta al menos un crítico, pero el alcance existe
  D  falta el alcance o no hay requisitos verificables
Un crítico "Parcial" sin supuesto escrito cuenta como "Falta".
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Estado = Literal["Cumple", "Parcial", "Falta", "N/A"]
Nota = Literal["A", "B", "C", "D"]

CRITICOS = ("P1", "P2", "P3", "P4", "T1", "T2", "D1")
TODOS = ("P1", "P2", "P3", "P4", "P5", "P6", "T1", "T2", "T3", "T4", "D1", "D2", "D3", "D4")


class Criterio(BaseModel):
    id: str = Field(description="P1..P6, T1..T4 o D1..D4")
    estado: Estado
    evidencia: str = Field(description="Sección o línea de la spec que lo respalda; vacío si no hay")
    correccion: str = Field(default="", description="Corrección mínima si no cumple")
    supuesto: str = Field(default="", description="Supuesto escrito que cierra un Parcial, si existe")


class RevisionSpec(BaseModel):
    criterios: list[Criterio]
    nota_llm: Nota = Field(description="La nota que tú le pondrías según la skill")
    vacios_graves: list[str] = Field(default_factory=list, description="Máximo tres, ordenados por impacto")
    resumen: str = ""


def calcular_nota(criterios: list[Criterio]) -> tuple[Nota, list[str]]:
    """Devuelve la nota y las razones. Un criterio crítico que no aparece cuenta como Falta."""
    por_id = {c.id.strip().upper(): c for c in criterios}
    razones: list[str] = []

    def efectivo(cid: str) -> str:
        c = por_id.get(cid)
        if c is None:
            razones.append(f"{cid}: no evaluado → cuenta como Falta")
            return "Falta"
        if c.estado == "Parcial" and cid in CRITICOS and not c.supuesto.strip():
            razones.append(f"{cid}: Parcial sin supuesto escrito → cuenta como Falta")
            return "Falta"
        if c.estado == "Cumple" and not c.evidencia.strip():
            razones.append(f"{cid}: marcado Cumple sin evidencia citada → cuenta como Falta")
            return "Falta"
        return c.estado

    estados = {cid: efectivo(cid) for cid in CRITICOS}

    if estados["P2"] == "Falta" or estados["T1"] == "Falta":
        razones.append("Falta el alcance (P2) o no hay aceptación observable (T1) → D")
        return "D", razones
    faltan = [cid for cid, e in estados.items() if e == "Falta"]
    if faltan:
        razones.append(f"Críticos que faltan: {', '.join(faltan)} → C")
        return "C", razones
    parciales = [cid for cid, e in estados.items() if e == "Parcial"]
    if parciales:
        razones.append(f"Críticos parciales con supuesto escrito: {', '.join(parciales)} → B")
        return "B", razones
    razones.append("Todos los críticos cumplen con evidencia → A")
    return "A", razones


def pasa(nota: Nota) -> bool:
    return nota in ("A", "B")
