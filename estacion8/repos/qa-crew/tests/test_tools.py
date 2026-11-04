import pytest

from qa_crew.main import DEV_PERMITIDAS, PLAN_PERMITIDAS, QA_PERMITIDAS, QA_PROTEGIDAS
from qa_crew.tools import CorrerPruebas, EscribirArchivo, LeerArchivo, Registro, correr_suite


@pytest.fixture
def root(tmp_path):
    for d in ("tests/features", "steps", "demo-app/lib", "demo-app/__tests__", "docs/tasks"):
        (tmp_path / d).mkdir(parents=True)
    return tmp_path


@pytest.mark.parametrize("ruta", ["tests/features/escalamiento.feature", "steps/escalamiento.steps.ts", "demo-app/__tests__/escalamiento.test.ts"])
def test_pruebas_escribe_sus_archivos(root, ruta):
    assert EscribirArchivo(root, QA_PERMITIDAS, QA_PROTEGIDAS)._run(ruta, "x").startswith("OK")


@pytest.mark.parametrize("ruta", ["demo-app/lib/agent.ts", "tests/features/asistente.feature", "demo-app/__tests__/agent.test.ts", "docs/tasks/x.md"])
def test_pruebas_no_escribe_fuera_de_su_rol(root, ruta):
    assert EscribirArchivo(root, QA_PERMITIDAS, QA_PROTEGIDAS)._run(ruta, "x").startswith("ERROR")


@pytest.mark.parametrize("ruta", ["tests/features/e.feature", "demo-app/__tests__/e.test.ts", "docs/tasks/001.md"])
def test_dev_solo_agent_ts(root, ruta):
    t = EscribirArchivo(root, DEV_PERMITIDAS)
    assert t._run(ruta, "x").startswith("ERROR")
    assert t._run("demo-app/lib/agent.ts", "// nuevo").startswith("OK")


def test_plan_solo_docs_tasks(root):
    t = EscribirArchivo(root, PLAN_PERMITIDAS)
    assert t._run("docs/tasks/task-package.yaml", "x").startswith("OK")
    assert t._run("demo-app/lib/agent.ts", "x").startswith("ERROR")
    assert t._run("AGENTS.md", "x").startswith("ERROR")


def test_no_sale_del_proyecto(root):
    assert LeerArchivo(root)._run("../../etc/passwd").startswith("ERROR")
    assert EscribirArchivo(root, ("*",))._run("../fuera.txt", "x").startswith("ERROR")


def test_solo_suites_de_la_lista(root):
    assert CorrerPruebas(root, Registro())._run("rm -rf /").startswith("ERROR")
    with pytest.raises(PermissionError):
        correr_suite(root, "deploy", Registro())
