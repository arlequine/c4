import shutil
from pathlib import Path

import pytest

from qa_crew.gate import cas_por_ola
from qa_crew.plan import validar_paquete

AQUI = Path(__file__).resolve().parents[1]
CAS = cas_por_ola((AQUI / "specs/escalamiento.md").read_text())
OLAS = {"ola-1": "A", "ola-2": "B"}
SUP = {"ola-2": ["El horario del escalamiento es fijo, lunes a viernes de 8:00 AM a 6:00 PM."]}


@pytest.fixture
def root(tmp_path):
    d = tmp_path / "docs/tasks"
    d.mkdir(parents=True)
    for f in (AQUI / "referencia/plan").iterdir():
        shutil.copy(f, d / f.name)
    return tmp_path


def test_paquete_de_referencia_es_valido(root):
    errores, orden = validar_paquete(root, OLAS, SUP, CAS)
    assert errores == []
    assert [t["id"] for t in orden] == ["TASK-001", "TASK-002"]


def test_ola_B_sin_supuesto_no_pasa(root):
    f = root / "docs/tasks/002-respuesta-en-el-chat.md"
    f.write_text("\n".join(l for l in f.read_text().splitlines() if not l.startswith("Supuesto:")))
    errores, _ = validar_paquete(root, OLAS, SUP, CAS)
    assert any("es B" in e for e in errores)


def test_ca_faltante_y_seccion_faltante(root):
    f = root / "docs/tasks/001-deteccion-intencion.md"
    f.write_text(f.read_text().replace("CA-04", "CA-XX").replace("## Test Plan", "## Pruebas"))
    errores, _ = validar_paquete(root, OLAS, SUP, CAS)
    assert any("CA-04" in e for e in errores) and any("Test Plan" in e for e in errores)


def test_dependencia_inexistente_y_ciclo(root):
    f1 = root / "docs/tasks/001-deteccion-intencion.md"
    f1.write_text(f1.read_text().replace("blockedBy: []", "blockedBy: [TASK-002]"))
    errores, _ = validar_paquete(root, OLAS, SUP, CAS)
    assert any("ciclo" in e for e in errores)
    f1.write_text(f1.read_text().replace("blockedBy: [TASK-002]", "blockedBy: [TASK-099]"))
    errores, _ = validar_paquete(root, OLAS, SUP, CAS)
    assert any("TASK-099" in e for e in errores)


def test_sin_manifiesto(tmp_path):
    errores, _ = validar_paquete(tmp_path, OLAS, SUP, CAS)
    assert errores == ["No existe docs/tasks/task-package.yaml"]
