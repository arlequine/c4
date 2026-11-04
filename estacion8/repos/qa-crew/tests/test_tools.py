import pytest

from qa_crew.tools import CorrerPruebas, EscribirArchivo, LeerArchivo, Registro, correr_suite
from qa_crew.main import DEV_PERMITIDAS, QA_PERMITIDAS, QA_PROTEGIDAS


@pytest.fixture
def root(tmp_path):
    (tmp_path / "tests/features").mkdir(parents=True)
    (tmp_path / "steps").mkdir()
    (tmp_path / "demo-app/lib").mkdir(parents=True)
    (tmp_path / "demo-app/lib/agent.ts").write_text("// original")
    return tmp_path


def test_qa_escribe_feature_nueva(root):
    t = EscribirArchivo(root, QA_PERMITIDAS, QA_PROTEGIDAS)
    assert t._run("tests/features/escalamiento.feature", "Feature: x").startswith("OK")
    assert t.escritos == ["tests/features/escalamiento.feature"]


@pytest.mark.parametrize("ruta", ["demo-app/lib/agent.ts", "tests/features/asistente.feature", "steps/asistente.steps.ts", "playwright.config.ts"])
def test_qa_no_escribe_fuera_de_su_rol(root, ruta):
    assert EscribirArchivo(root, QA_PERMITIDAS, QA_PROTEGIDAS)._run(ruta, "x").startswith("ERROR")


@pytest.mark.parametrize("ruta", ["tests/features/escalamiento.feature", "steps/nuevo.steps.ts", "demo-app/app/page.tsx"])
def test_dev_solo_escribe_agent_ts(root, ruta):
    t = EscribirArchivo(root, DEV_PERMITIDAS)
    assert t._run(ruta, "x").startswith("ERROR")
    assert t._run("demo-app/lib/agent.ts", "// nuevo").startswith("OK")


def test_no_sale_del_proyecto(root):
    assert LeerArchivo(root)._run("../../etc/passwd").startswith("ERROR")
    assert EscribirArchivo(root, ("*",))._run("../fuera.txt", "x").startswith("ERROR")


def test_solo_suites_de_la_lista(root):
    out = CorrerPruebas(root, Registro())._run("rm -rf /")
    assert out.startswith("ERROR")
    with pytest.raises(PermissionError):
        correr_suite(root, "deploy", Registro())
