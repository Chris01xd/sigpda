"""
Pruebas de las tablas normalizadas de IA (Fase 7) y su persistencia.
Usa una base de datos SQLite temporal y aislada: NUNCA toca
database/sigpda.db (los datos reales del sistema).
"""
import pandas as pd
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from database.modelos import (
    Base,
    EjecucionEntrenamiento,
    ResultadoModelo,
    ResultadoFold,
    ResultadoPruebaEstadistica,
    ModeloGuardado,
    # Tablas preexistentes: deben seguir intactas junto a las nuevas.
    Plato,
    ComparacionModelos,
)
import ia.persistencia_bd as persistencia_bd


@pytest.fixture()
def sesion_prueba(tmp_path, monkeypatch):
    """Base de datos SQLite temporal, aislada de sigpda.db, con TODAS las tablas."""
    ruta_db = tmp_path / "test_sigpda.db"
    engine = create_engine(f"sqlite:///{ruta_db}")
    Base.metadata.create_all(engine)
    SesionPrueba = sessionmaker(bind=engine)
    monkeypatch.setattr(persistencia_bd, "obtener_sesion", lambda: SesionPrueba())
    yield SesionPrueba, engine


class TestEsquemaTablas:
    def test_crear_tablas_incluye_las_nuevas_y_las_existentes(self, sesion_prueba):
        _Sesion, engine = sesion_prueba
        tablas = set(inspect(engine).get_table_names())

        nuevas = {
            "ejecuciones_entrenamiento", "resultados_modelo",
            "resultados_fold", "resultados_prueba_estadistica", "modelos_guardados",
        }
        preexistentes = {"platos", "ventas", "comparaciones_modelos", "predicciones"}

        assert nuevas.issubset(tablas)
        assert preexistentes.issubset(tablas)  # no se eliminó nada existente

    def test_comparacion_modelos_original_no_fue_modificada(self, sesion_prueba):
        """La tabla del endpoint /comparar-modelos (3 modelos) sigue existiendo intacta."""
        _Sesion, engine = sesion_prueba
        columnas = {c["name"] for c in inspect(engine).get_columns("comparaciones_modelos")}
        assert {"mae_arima", "mae_prophet", "mae_transformer", "modelo_ganador"}.issubset(columnas)


def _resultado_comparacion_falso():
    fechas = pd.date_range("2026-01-01", periods=40, freq="D")
    serie = pd.DataFrame({"fecha": fechas, "cantidad": range(40)})
    df_plato = pd.DataFrame({"id_plato": 1, "fecha": fechas, "cantidad": range(40)})
    return {
        "modelo_ganador": "holt_winters",
        "criterio_seleccion": "menor MAE",
        "metricas_por_modelo": {
            "arima": {"mae": 3.0, "rmse": 3.5, "mape": 20.0, "smape": 18.0, "r2": 0.7},
            "prophet": {"mae": 4.0, "rmse": 4.2, "mape": 25.0, "smape": 22.0, "r2": 0.6},
            "holt_winters": {"mae": 2.0, "rmse": 2.5, "mape": 15.0, "smape": 14.0, "r2": 0.8},
            "transformer_random_forest": {"mae": None, "rmse": None, "mape": None, "smape": None, "r2": None, "error": "datos insuficientes"},
            "transformer_gradient_boosting": {"mae": 2.5, "rmse": 2.8, "mape": 17.0, "smape": 16.0, "r2": 0.75},
        },
        "info_modelos": {
            "arima": {"orden": "ARIMA(1,1,1)"},
            "holt_winters": {"hiperparametros": {"trend": "add"}},
        },
        "_serie": serie,
        "_df_plato": df_plato,
    }


class TestGuardarEjecucionComparacion:
    def test_crea_ejecucion_y_un_resultado_por_modelo(self, sesion_prueba):
        Sesion, _engine = sesion_prueba
        resultado = _resultado_comparacion_falso()

        id_ejecucion = persistencia_bd.guardar_ejecucion_comparacion(
            id_plato=1, id_usuario=1, resultado_comparacion=resultado,
            dias_adelante=7, clima=2, evento=0, duracion_segundos=1.23,
        )

        sesion = Sesion()
        try:
            ejecucion = sesion.get(EjecucionEntrenamiento, id_ejecucion)
            assert ejecucion is not None
            assert ejecucion.modelo_ganador == "holt_winters"
            assert ejecucion.id_plato == 1

            resultados = sesion.query(ResultadoModelo).filter_by(id_ejecucion=id_ejecucion).all()
            assert len(resultados) == 5
            nombres = {r.modelo for r in resultados}
            assert nombres == {
                "arima", "prophet", "holt_winters",
                "transformer_random_forest", "transformer_gradient_boosting",
            }

            ganador_row = next(r for r in resultados if r.modelo == "holt_winters")
            assert ganador_row.posicion == 1  # menor MAE
            assert ganador_row.categoria == "clasico"

            hibrido_row = next(r for r in resultados if r.modelo == "transformer_random_forest")
            assert hibrido_row.categoria == "hibrido"
            assert hibrido_row.error_mensaje == "datos insuficientes"
            assert hibrido_row.posicion is None  # no tiene MAE válido, no entra al ranking
        finally:
            sesion.close()

    def test_guarda_folds_si_se_proporcionan(self, sesion_prueba):
        Sesion, _engine = sesion_prueba
        resultado = _resultado_comparacion_falso()
        # Las fechas llegan como strings ISO (igual que ia.validacion.evaluar_modelo_cv
        # las produce vía .isoformat()); persistencia_bd debe convertirlas a date
        # antes de insertarlas (columnas SQLAlchemy Date). Este es un caso de
        # regresión: guardar strings sin convertir rompe la inserción en SQLite.
        folds_por_modelo = {
            "holt_winters": {
                "folds": [
                    {
                        "numero_fold": 1, "n_train": 20, "n_val": 5, "mae": 2.1,
                        "tiempo_entrenamiento": 0.05,
                        "fecha_inicio_train": "2026-01-01", "fecha_fin_train": "2026-01-20",
                        "fecha_inicio_val": "2026-01-21", "fecha_fin_val": "2026-01-25",
                    },
                    {
                        "numero_fold": 2, "n_train": 25, "n_val": 5, "mae": 1.9,
                        "tiempo_entrenamiento": 0.06,
                        "fecha_inicio_train": "2026-01-01", "fecha_fin_train": "2026-01-25",
                        "fecha_inicio_val": "2026-01-26", "fecha_fin_val": "2026-01-30",
                    },
                ]
            }
        }

        id_ejecucion = persistencia_bd.guardar_ejecucion_comparacion(
            id_plato=1, id_usuario=1, resultado_comparacion=resultado,
            dias_adelante=7, clima=2, evento=0, folds_por_modelo=folds_por_modelo,
        )

        sesion = Sesion()
        try:
            resultado_hw = sesion.query(ResultadoModelo).filter_by(
                id_ejecucion=id_ejecucion, modelo="holt_winters",
            ).first()
            folds = sesion.query(ResultadoFold).filter_by(
                id_resultado_modelo=resultado_hw.id_resultado_modelo,
            ).all()
            assert len(folds) == 2
            assert {f.numero_fold for f in folds} == {1, 2}
            import datetime as _dt
            assert isinstance(folds[0].fecha_inicio_train, _dt.date)
            assert folds[0].fecha_inicio_train.isoformat() == "2026-01-01"
        finally:
            sesion.close()

    def test_guarda_pruebas_estadisticas(self, sesion_prueba):
        Sesion, _engine = sesion_prueba
        resultado = _resultado_comparacion_falso()
        pruebas = [
            {"prueba": "friedman", "estadistico": 5.2, "p_valor": 0.02, "significativo": True, "interpretacion": "..."},
            {"prueba": "wilcoxon", "modelo_a": "holt_winters", "modelo_b": "arima",
             "estadistico": 3.0, "p_valor": 0.03, "p_valor_ajustado": 0.06, "significativo": False},
        ]

        id_ejecucion = persistencia_bd.guardar_ejecucion_comparacion(
            id_plato=1, id_usuario=1, resultado_comparacion=resultado,
            dias_adelante=7, clima=2, evento=0, pruebas_estadisticas=pruebas,
        )

        sesion = Sesion()
        try:
            filas = sesion.query(ResultadoPruebaEstadistica).filter_by(id_ejecucion=id_ejecucion).all()
            assert len(filas) == 2
            wilcoxon = next(f for f in filas if f.prueba == "wilcoxon")
            assert wilcoxon.modelo_a == "holt_winters"
            assert wilcoxon.p_valor_ajustado == 0.06
        finally:
            sesion.close()


class TestGuardarRegistroModeloGuardado:
    def test_desactiva_registros_previos_del_mismo_plato(self, sesion_prueba):
        Sesion, _engine = sesion_prueba

        persistencia_bd.guardar_registro_modelo_guardado(
            id_plato=1, id_ejecucion=None, modelo="arima", hash_datos="h1",
        )
        persistencia_bd.guardar_registro_modelo_guardado(
            id_plato=1, id_ejecucion=None, modelo="prophet", hash_datos="h2",
        )

        sesion = Sesion()
        try:
            registros = sesion.query(ModeloGuardado).filter_by(id_plato=1).all()
            assert len(registros) == 2
            activos = [r for r in registros if r.activo]
            assert len(activos) == 1
            assert activos[0].modelo == "prophet"
            assert activos[0].ruta == "models/plato_1"  # ruta lógica, no absoluta
        finally:
            sesion.close()

    def test_no_afecta_registros_de_otro_plato(self, sesion_prueba):
        Sesion, _engine = sesion_prueba
        persistencia_bd.guardar_registro_modelo_guardado(id_plato=1, id_ejecucion=None, modelo="arima", hash_datos="h1")
        persistencia_bd.guardar_registro_modelo_guardado(id_plato=2, id_ejecucion=None, modelo="prophet", hash_datos="h2")

        sesion = Sesion()
        try:
            activos_plato_1 = sesion.query(ModeloGuardado).filter_by(id_plato=1, activo=True).all()
            assert len(activos_plato_1) == 1
        finally:
            sesion.close()
