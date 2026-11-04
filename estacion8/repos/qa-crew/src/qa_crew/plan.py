"""Validación del paquete de create-implementation-plan (paso 6 de la skill), hecha por código."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

CAMPOS = ("id", "title", "milestone", "priority", "estimate", "blockedBy", "blocks", "areas", "parent")
SECCIONES = ("## Summary", "## Scope", "## Deliverables", "## Acceptance Criteria", "## Test Plan", "## Context", "## Definition of Ready")


def leer_tarea(p: Path) -> tuple[dict, str]:
    texto = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, flags=re.S)
    if not m:
        raise ValueError("sin frontmatter")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def validar_paquete(root: Path, olas_que_pasan: dict[str, str], supuestos_b: dict[str, list[str]], cas: dict[str, list[str]]) -> tuple[list[str], list[dict]]:
    """Devuelve (errores, tareas en orden de dependencias).

    olas_que_pasan: {'ola-1': 'A', 'ola-2': 'B'}
    supuestos_b: {'ola-2': ['el horario es fijo …']}
    cas: {'ola-1': ['CA-01', …]}
    """
    errores: list[str] = []
    manifiesto = root / "docs/tasks/task-package.yaml"
    if not manifiesto.exists():
        return ["No existe docs/tasks/task-package.yaml"], []
    try:
        pkg = yaml.safe_load(manifiesto.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return [f"task-package.yaml no es YAML válido: {e}"], []
    for k in ("planningWave", "tasksDir", "milestones", "tasks"):
        if k not in pkg:
            errores.append(f"task-package.yaml sin '{k}'")
    if not (root / "docs/tasks/milestones.md").exists():
        errores.append("No existe docs/tasks/milestones.md")
    milestones = set(pkg.get("milestones") or [])
    tareas: list[dict] = []
    ids: set[str] = set()
    for t in pkg.get("tasks") or []:
        f = root / str(t.get("file", ""))
        if not f.is_file():
            errores.append(f"{t.get('id')}: no existe {t.get('file')}")
            continue
        try:
            fm, cuerpo = leer_tarea(f)
        except Exception as e:  # noqa: BLE001
            errores.append(f"{t.get('file')}: {e}")
            continue
        for c in CAMPOS:
            if c not in fm:
                errores.append(f"{fm.get('id', f.name)}: falta '{c}' en el frontmatter")
        for s in SECCIONES:
            if s not in cuerpo:
                errores.append(f"{fm.get('id', f.name)}: falta la sección '{s}'")
        if fm.get("id") in ids:
            errores.append(f"ID repetido: {fm.get('id')}")
        ids.add(fm.get("id"))
        if fm.get("id") != t.get("id"):
            errores.append(f"{t.get('file')}: el id del archivo ({fm.get('id')}) no coincide con el manifiesto ({t.get('id')})")
        if fm.get("milestone") not in milestones:
            errores.append(f"{fm.get('id')}: milestone '{fm.get('milestone')}' no está en task-package.yaml")
        tareas.append({**fm, "file": str(t.get("file")), "cuerpo": cuerpo})

    por_id = {t["id"]: t for t in tareas}
    for t in tareas:
        for campo in ("blockedBy", "blocks"):
            for d in t.get(campo) or []:
                if d not in por_id:
                    errores.append(f"{t['id']}: {campo} apunta a {d}, que no está en el manifiesto")
        if t.get("parent") and t["parent"] not in por_id:
            errores.append(f"{t['id']}: parent {t['parent']} no está en el manifiesto")

    # cada ola que pasa tiene tareas (areas: [ola-N]) y sus CA aparecen en los Acceptance Criteria
    for ola, nota in olas_que_pasan.items():
        suyas = [t for t in tareas if ola in (t.get("areas") or [])]
        if not suyas:
            errores.append(f"{ola} (nota {nota}) no tiene ninguna tarea con areas: [{ola}]")
            continue
        texto = "\n".join(t["cuerpo"] for t in suyas)
        for ca in cas.get(ola, []):
            if ca not in texto:
                errores.append(f"{ola}: {ca} no aparece en ninguna tarea")
        if nota == "B":
            if "supuesto" not in texto.lower():
                errores.append(f"{ola} es B: sus tareas deben registrar el supuesto (la palabra 'Supuesto' y el texto)")
            for s in supuestos_b.get(ola, []):
                clave = " ".join(s.split()[:4]).lower()
                if clave and clave not in texto.lower():
                    errores.append(f"{ola} es B: el supuesto «{s[:60]}…» no está escrito en sus tareas")

    orden, ciclo = orden_topologico(tareas)
    if ciclo:
        errores.append(f"Hay un ciclo de dependencias entre: {', '.join(ciclo)}")
    return errores, orden


def orden_topologico(tareas: list[dict]) -> tuple[list[dict], list[str]]:
    por_id = {t["id"]: t for t in tareas}
    pendientes = {t["id"]: {d for d in (t.get("blockedBy") or []) if d in por_id} for t in tareas}
    orden: list[dict] = []
    while pendientes:
        listos = sorted(i for i, deps in pendientes.items() if not deps)
        if not listos:
            return orden, sorted(pendientes)
        for i in listos:
            orden.append(por_id[i])
            pendientes.pop(i)
        for deps in pendientes.values():
            deps.difference_update(listos)
    return orden, []
