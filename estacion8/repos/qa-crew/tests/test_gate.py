from pathlib import Path

from qa_crew.gate import (CRITICOS, TODOS, Criterio, RevisionSpec, ResultadoTest, calcular_nota, cas_por_ola,
                          cobertura, pasa, supuestos, veredicto_por_ca)

AQUI = Path(__file__).resolve().parents[1]


def _crit(**cambios):
    out = []
    for cid in TODOS:
        e, sup = cambios.get(cid, ("Cumple", ""))
        out.append(Criterio(id=cid, estado=e, evidencia="" if e == "Falta" else f"§ {cid}", supuesto=sup))
    return out


def test_A_B_C_D():
    assert calcular_nota(_crit())[0] == "A"
    assert calcular_nota(_crit(T2=("Parcial", "horario fijo")))[0] == "B"
    assert calcular_nota(_crit(P4=("Parcial", "")))[0] == "C"
    assert calcular_nota(_crit(D1=("Falta", "")))[0] == "C"
    assert calcular_nota(_crit(P2=("Falta", "")))[0] == "D"
    assert calcular_nota(_crit(T1=("Falta", "")))[0] == "D"


def test_cumple_sin_evidencia_y_critico_omitido_no_cuentan():
    c = _crit()
    c[0].evidencia = ""
    assert calcular_nota(c)[0] == "C"
    assert calcular_nota([x for x in _crit() if x.id != "P3"])[0] == "C"


def test_no_criticos_no_bajan_la_nota():
    assert calcular_nota(_crit(P5=("Falta", ""), T3=("Falta", "")))[0] == "A"
    assert set(CRITICOS) < set(TODOS)


def test_pasan_A_y_B():
    assert pasa("A") and pasa("B") and not pasa("C") and not pasa("D")


def test_referencia_da_A_B_C():
    rev = RevisionSpec.model_validate_json((AQUI / "referencia/revision.json").read_text())
    assert [calcular_nota(o.criterios)[0] for o in rev.olas] == ["A", "B", "C"]
    assert supuestos(rev.olas[1]) and not supuestos(rev.olas[0])


def test_cas_por_ola_desde_la_spec():
    cas = cas_por_ola((AQUI / "specs/escalamiento.md").read_text())
    assert cas == {"ola-1": ["CA-01", "CA-02", "CA-03", "CA-04"], "ola-2": ["CA-05", "CA-06"], "ola-3": ["CA-07"]}


def test_cobertura_y_veredicto():
    res = [ResultadoTest(nombre="x > CA-01 algo", ok=True, suite="unit"), ResultadoTest(nombre="CA-02 a", ok=True, suite="unit"),
           ResultadoTest(nombre="CA-02 b", ok=False, suite="bdd")]
    assert cobertura(["CA-01", "CA-03"], [r.nombre for r in res]) == {"CA-01": ["x > CA-01 algo"], "CA-03": []}
    assert veredicto_por_ca(["CA-01", "CA-02", "CA-03"], res) == {"CA-01": True, "CA-02": False, "CA-03": None}
