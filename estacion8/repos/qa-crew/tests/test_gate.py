from qa_crew.gate import CRITICOS, TODOS, Criterio, calcular_nota


def _todos(estado="Cumple", **cambios):
    out = []
    for cid in TODOS:
        e, sup = cambios.get(cid, (estado, ""))
        out.append(Criterio(id=cid, estado=e, evidencia="" if e == "Falta" else f"§ {cid}", supuesto=sup))
    return out


def test_todo_cumple_es_A():
    assert calcular_nota(_todos())[0] == "A"


def test_parcial_critico_con_supuesto_es_B():
    assert calcular_nota(_todos(T2=("Parcial", "longitud en caracteres Unicode")))[0] == "B"


def test_parcial_critico_sin_supuesto_cuenta_como_falta():
    assert calcular_nota(_todos(P4=("Parcial", "")))[0] == "C"


def test_falta_critico_es_C():
    assert calcular_nota(_todos(D1=("Falta", "")))[0] == "C"


def test_sin_alcance_o_sin_aceptacion_es_D():
    assert calcular_nota(_todos(P2=("Falta", "")))[0] == "D"
    assert calcular_nota(_todos(T1=("Falta", "")))[0] == "D"


def test_cumple_sin_evidencia_no_cuenta():
    c = _todos()
    next(x for x in c if x.id == "P1").evidencia = ""
    assert calcular_nota(c)[0] == "C"


def test_critico_omitido_cuenta_como_falta():
    c = [x for x in _todos() if x.id != "P3"]
    assert calcular_nota(c)[0] == "C"


def test_no_criticos_no_bajan_la_nota():
    assert calcular_nota(_todos(P5=("Falta", ""), T3=("Falta", ""), D3=("N/A", "")))[0] == "A"
    assert set(CRITICOS) < set(TODOS)
