"""
Pruebas de los endpoints principales del módulo de IA: autenticación
y permisos, y las rutas que no requieren entrenar modelos pesados
(EDA de un plato inexistente, modelos guardados). Los flujos costosos
(/comparar-modelos, /entrenar-comparar) ya están cubiertos por pruebas
unitarias rápidas con datos sintéticos (test_comparacion_completa.py,
test_orquestador.py) y se verificaron manualmente end-to-end contra
datos reales durante el desarrollo; no se repiten aquí para no hacer
lenta la suite completa.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth import obtener_usuario_actual


@pytest.fixture()
def client_autenticado():
    app.dependency_overrides[obtener_usuario_actual] = lambda: {"sub": "1", "usuario": "admin", "rol": "administrador"}
    yield TestClient(app)
    app.dependency_overrides.pop(obtener_usuario_actual, None)


@pytest.fixture()
def client_sin_auth():
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    return TestClient(app)


class TestAutenticacionRequerida:
    """Los endpoints de IA deben exigir autenticación, igual que el resto del sistema."""

    @pytest.mark.parametrize("metodo,ruta", [
        ("get", "/api/ia/platos-disponibles"),
        ("get", "/api/ia/eda/1"),
        ("get", "/api/ia/modelos-guardados"),
        ("get", "/api/ia/modelos-guardados/1"),
        ("post", "/api/ia/predecir"),
        ("post", "/api/ia/comparar-modelos"),
        ("post", "/api/ia/entrenar-comparar"),
        ("post", "/api/ia/modelos-guardados/1/predecir"),
        ("post", "/api/ia/modelos-guardados/1/reentrenar"),
        ("get", "/api/reportes/ia/1/pdf"),
        ("get", "/api/reportes/ia/1/word"),
        ("get", "/api/reportes/ia/1/excel"),
    ])
    def test_endpoint_requiere_token(self, client_sin_auth, metodo, ruta):
        if metodo == "post":
            r = client_sin_auth.post(ruta, json={})
        else:
            r = client_sin_auth.get(ruta)
        assert r.status_code == 401


class TestEndpointsLivianos:
    """Endpoints que no requieren entrenar modelos: rápidos de probar en la suite completa."""

    def test_platos_disponibles(self, client_autenticado):
        r = client_autenticado.get("/api/ia/platos-disponibles")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_eda_plato_inexistente_da_404(self, client_autenticado):
        r = client_autenticado.get("/api/ia/eda/999999")
        assert r.status_code == 404

    def test_modelos_guardados_lista_es_json(self, client_autenticado):
        r = client_autenticado.get("/api/ia/modelos-guardados")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_modelo_guardado_detalle_inexistente_da_404(self, client_autenticado):
        r = client_autenticado.get("/api/ia/modelos-guardados/999999")
        assert r.status_code == 404

    def test_modelo_guardado_predecir_sin_modelo_da_404(self, client_autenticado):
        r = client_autenticado.post("/api/ia/modelos-guardados/999999/predecir", json={"dias_adelante": 5})
        assert r.status_code == 404

    def test_reporte_ia_pdf_ejecucion_inexistente_da_404(self, client_autenticado):
        r = client_autenticado.get("/api/reportes/ia/999999/pdf")
        assert r.status_code == 404

    def test_reporte_ia_word_ejecucion_inexistente_da_404(self, client_autenticado):
        r = client_autenticado.get("/api/reportes/ia/999999/word")
        assert r.status_code == 404

    def test_reporte_ia_excel_ejecucion_inexistente_da_404(self, client_autenticado):
        r = client_autenticado.get("/api/reportes/ia/999999/excel")
        assert r.status_code == 404

    def test_comparar_modelos_datos_insuficientes_da_400(self, client_autenticado):
        r = client_autenticado.post(
            "/api/ia/comparar-modelos", json={"id_plato": 999999, "dias_adelante": 5, "clima": 2, "evento": 0},
        )
        assert r.status_code == 400

    def test_entrenar_comparar_datos_insuficientes_da_400(self, client_autenticado):
        r = client_autenticado.post(
            "/api/ia/entrenar-comparar",
            json={"id_plato": 999999, "dias_adelante": 5, "n_splits": 2, "ejecutar_tuning": False, "guardar_ganador": False},
        )
        assert r.status_code == 400
