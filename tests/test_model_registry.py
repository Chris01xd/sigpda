"""
Pruebas de ia/model_registry.py: guardado/carga atómicos, detección
de vigencia por hash de datos, listado, eliminación segura y
protección contra path traversal. Usa un directorio temporal aislado
(no toca la carpeta models/ real del proyecto).
"""
import numpy as np
import pytest

import ia.model_registry as registry


@pytest.fixture(autouse=True)
def _models_dir_aislado(tmp_path, monkeypatch):
    """Aísla cada prueba en su propio directorio temporal de modelos."""
    monkeypatch.setattr(registry, "MODELS_DIR", tmp_path / "models")
    yield


class _ModeloFalso:
    """Objeto picklable simple, simula un modelo entrenado (p. ej. ExponentialSmoothingResults)."""
    def __init__(self, valor_base=5.0):
        self.valor_base = valor_base

    def forecast(self, steps):
        return np.full(steps, self.valor_base)


class TestGuardarYCargarModelo:
    def test_roundtrip_basico(self):
        modelo = _ModeloFalso(7.0)
        resultado = registry.guardar_modelo(
            id_plato=1, nombre_plato="Ceviche", tipo_modelo="holt_winters",
            modelo_objeto=modelo, hiperparametros={"trend": "add"},
            metricas={"mae": 1.2, "rmse": 1.5, "mape": 10.0, "smape": 9.0, "r2": 0.8},
            n_registros=60, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-03-01",
            hash_datos="abc123",
        )
        assert resultado["guardado"] is True

        cargado = registry.cargar_modelo(1)
        assert cargado is not None
        modelo_cargado, metadata = cargado
        assert modelo_cargado.forecast(3).tolist() == [7.0, 7.0, 7.0]
        assert metadata["tipo_modelo"] == "holt_winters"
        assert metadata["nombre_plato"] == "Ceviche"
        assert metadata["hash_datos"] == "abc123"
        assert "versiones_librerias" in metadata
        assert "ruta_artefacto" not in metadata

    def test_cargar_modelo_inexistente_retorna_none(self):
        assert registry.cargar_modelo(999) is None

    def test_tipo_modelo_invalido_lanza_error(self):
        with pytest.raises(ValueError):
            registry.guardar_modelo(
                id_plato=1, nombre_plato="X", tipo_modelo="modelo_falso_no_soportado",
                modelo_objeto=_ModeloFalso(), hiperparametros={}, metricas={},
                n_registros=1, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-01",
                hash_datos="x",
            )

    def test_guardar_sobrescribe_el_modelo_anterior(self):
        registry.guardar_modelo(
            id_plato=2, nombre_plato="X", tipo_modelo="arima",
            modelo_objeto=_ModeloFalso(1.0), hiperparametros={}, metricas={"mae": 5.0},
            n_registros=30, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-30",
            hash_datos="v1",
        )
        registry.guardar_modelo(
            id_plato=2, nombre_plato="X", tipo_modelo="prophet",
            modelo_objeto=_ModeloFalso(2.0), hiperparametros={}, metricas={"mae": 3.0},
            n_registros=40, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-02-10",
            hash_datos="v2",
        )
        _modelo, metadata = registry.cargar_modelo(2)
        assert metadata["tipo_modelo"] == "prophet"
        assert metadata["hash_datos"] == "v2"

    def test_no_deja_archivos_temporales_tras_guardar(self):
        registry.guardar_modelo(
            id_plato=3, nombre_plato="X", tipo_modelo="arima",
            modelo_objeto=_ModeloFalso(), hiperparametros={}, metricas={},
            n_registros=1, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-01",
            hash_datos="x",
        )
        directorio = registry._ruta_plato(3)
        temporales = list(directorio.glob(".tmp_*"))
        assert temporales == []


class TestExisteModeloVigente:
    def test_sin_modelo_guardado(self):
        r = registry.existe_modelo_vigente(42)
        assert r["existe"] is False
        assert r["recomienda_reentrenar"] is True

    def test_con_modelo_y_sin_verificar_hash(self):
        registry.guardar_modelo(
            id_plato=4, nombre_plato="X", tipo_modelo="arima",
            modelo_objeto=_ModeloFalso(), hiperparametros={}, metricas={"mae": 1.0},
            n_registros=30, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-30",
            hash_datos="hash-original",
        )
        r = registry.existe_modelo_vigente(4)
        assert r["existe"] is True
        assert r["vigente"] is True
        assert r["recomienda_reentrenar"] is False

    def test_datos_cambiados_recomienda_reentrenar(self):
        registry.guardar_modelo(
            id_plato=5, nombre_plato="X", tipo_modelo="arima",
            modelo_objeto=_ModeloFalso(), hiperparametros={}, metricas={"mae": 1.0},
            n_registros=30, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-30",
            hash_datos="hash-original",
        )
        r = registry.existe_modelo_vigente(5, hash_datos_actual="hash-nuevo-porque-cambiaron-los-datos")
        assert r["existe"] is True
        assert r["vigente"] is False
        assert r["recomienda_reentrenar"] is True

    def test_datos_sin_cambios_sigue_vigente(self):
        registry.guardar_modelo(
            id_plato=6, nombre_plato="X", tipo_modelo="arima",
            modelo_objeto=_ModeloFalso(), hiperparametros={}, metricas={"mae": 1.0},
            n_registros=30, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-30",
            hash_datos="hash-igual",
        )
        r = registry.existe_modelo_vigente(6, hash_datos_actual="hash-igual")
        assert r["vigente"] is True
        assert r["recomienda_reentrenar"] is False


class TestListarYEliminar:
    def test_lista_vacia_inicialmente(self):
        assert registry.listar_modelos_guardados() == []

    def test_lista_incluye_modelos_guardados(self):
        registry.guardar_modelo(
            id_plato=7, nombre_plato="A", tipo_modelo="arima",
            modelo_objeto=_ModeloFalso(), hiperparametros={}, metricas={},
            n_registros=1, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-01",
            hash_datos="x",
        )
        registry.guardar_modelo(
            id_plato=8, nombre_plato="B", tipo_modelo="prophet",
            modelo_objeto=_ModeloFalso(), hiperparametros={}, metricas={},
            n_registros=1, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-01",
            hash_datos="y",
        )
        lista = registry.listar_modelos_guardados()
        ids = {m["id_plato"] for m in lista}
        assert ids == {7, 8}

    def test_eliminar_modelo_existente(self):
        registry.guardar_modelo(
            id_plato=9, nombre_plato="A", tipo_modelo="arima",
            modelo_objeto=_ModeloFalso(), hiperparametros={}, metricas={},
            n_registros=1, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-01",
            hash_datos="x",
        )
        r = registry.eliminar_modelo(9)
        assert r["eliminado"] is True
        assert registry.cargar_modelo(9) is None

    def test_eliminar_modelo_inexistente(self):
        r = registry.eliminar_modelo(999)
        assert r["eliminado"] is False


class TestProteccionPathTraversal:
    def test_id_plato_no_numerico_lanza_error(self):
        with pytest.raises(ValueError):
            registry._ruta_plato("../../etc/passwd")

    def test_id_plato_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            registry._ruta_plato(-1)

    def test_id_plato_cero_lanza_error(self):
        with pytest.raises(ValueError):
            registry._ruta_plato(0)

    def test_ruta_resultante_siempre_dentro_de_models_dir(self):
        ruta = registry._ruta_plato(42)
        assert registry.MODELS_DIR.resolve() in ruta.resolve().parents


class TestCalcularHashDataset:
    def test_deterministico(self):
        h1 = registry.calcular_hash_dataset(100, "2026-01-01", "2026-03-01", 543.21)
        h2 = registry.calcular_hash_dataset(100, "2026-01-01", "2026-03-01", 543.21)
        assert h1 == h2

    def test_cambia_si_cambian_los_datos(self):
        h1 = registry.calcular_hash_dataset(100, "2026-01-01", "2026-03-01", 543.21)
        h2 = registry.calcular_hash_dataset(105, "2026-01-01", "2026-03-05", 560.00)
        assert h1 != h2


class TestPredecirConModeloGuardado:
    def test_sin_modelo_guardado_retorna_error(self):
        r = registry.predecir_con_modelo_guardado(123, dias_adelante=5)
        assert "error" in r

    def test_predice_con_modelo_tipo_forecast(self):
        registry.guardar_modelo(
            id_plato=10, nombre_plato="X", tipo_modelo="holt_winters",
            modelo_objeto=_ModeloFalso(4.0), hiperparametros={}, metricas={"mae": 1.5},
            n_registros=30, fecha_inicio_datos="2026-01-01", fecha_fin_datos="2026-01-30",
            hash_datos="x",
        )
        r = registry.predecir_con_modelo_guardado(10, dias_adelante=3)
        assert r["usando_modelo_guardado"] is True
        assert len(r["predicciones_futuras"]) == 3
        assert all(p["demanda_estimada"] == 4.0 for p in r["predicciones_futuras"])
