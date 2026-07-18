"""
=================================================================
SIGPDA - Modelos ORM (SQLAlchemy)
=================================================================
Todas las tablas y campos están EN ESPAÑOL conforme a los
requerimientos del proyecto de tesis.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    Text, ForeignKey, Numeric
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ==================================================================
# 1. ROLES Y PERMISOS
# ==================================================================
class Rol(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255))
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuarios = relationship("Usuario", back_populates="rol")
    permisos = relationship("Permiso", back_populates="rol")


class Permiso(Base):
    __tablename__ = "permisos"

    id_permiso = Column(Integer, primary_key=True, autoincrement=True)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    modulo = Column(String(50), nullable=False)
    accion = Column(String(30), nullable=False)  # ver/crear/editar/eliminar/exportar/generar_reporte

    rol = relationship("Rol", back_populates="permisos")


# ==================================================================
# 2. USUARIOS
# ==================================================================
class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(80), nullable=False)
    apellido = Column(String(80), nullable=False)
    correo = Column(String(120), unique=True, nullable=False)
    usuario = Column(String(60), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)  # cifrada con bcrypt
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    ultimo_acceso = Column(DateTime, nullable=True)

    rol = relationship("Rol", back_populates="usuarios")
    sesiones = relationship("Sesion", back_populates="usuario")
    bitacoras = relationship("Bitacora", back_populates="usuario")


class Sesion(Base):
    __tablename__ = "sesiones"

    id_sesion = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    fecha_ingreso = Column(DateTime, default=datetime.utcnow)
    fecha_salida = Column(DateTime, nullable=True)
    ip_equipo = Column(String(45))
    estado = Column(String(20), default="activa")  # activa / cerrada

    usuario = relationship("Usuario", back_populates="sesiones")


# ==================================================================
# 3. PYMES / RESTAURANTES
# ==================================================================
class Restaurante(Base):
    __tablename__ = "restaurantes"

    id_restaurante = Column(Integer, primary_key=True, autoincrement=True)
    nombre_comercial = Column(String(150), nullable=False)
    ruc = Column(String(15), unique=True)
    direccion = Column(String(200))
    distrito = Column(String(80))
    provincia = Column(String(80))
    responsable = Column(String(150))
    telefono = Column(String(20))
    correo = Column(String(120))
    estado = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    platos = relationship("Plato", back_populates="restaurante")
    insumos = relationship("Insumo", back_populates="restaurante")
    ventas = relationship("Venta", back_populates="restaurante")


# ==================================================================
# 4. PLATOS
# ==================================================================
class Plato(Base):
    __tablename__ = "platos"

    id_plato = Column(Integer, primary_key=True, autoincrement=True)
    id_restaurante = Column(Integer, ForeignKey("restaurantes.id_restaurante"))
    nombre = Column(String(120), nullable=False)
    categoria = Column(String(60))
    descripcion = Column(Text)
    precio_venta = Column(Numeric(10, 2), nullable=False)
    costo_estimado = Column(Numeric(10, 2), default=0)
    tiempo_preparacion_min = Column(Integer, default=0)
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    restaurante = relationship("Restaurante", back_populates="platos")
    recetas = relationship("Receta", back_populates="plato")
    detalles_venta = relationship("DetalleVenta", back_populates="plato")
    producciones = relationship("Produccion", back_populates="plato")


# ==================================================================
# 5. INSUMOS
# ==================================================================
class Insumo(Base):
    __tablename__ = "insumos"

    id_insumo = Column(Integer, primary_key=True, autoincrement=True)
    id_restaurante = Column(Integer, ForeignKey("restaurantes.id_restaurante"))
    id_proveedor = Column(Integer, ForeignKey("proveedores.id_proveedor"), nullable=True)
    nombre = Column(String(120), nullable=False)
    categoria = Column(String(60))
    unidad_medida = Column(String(20), nullable=False)
    stock_disponible = Column(Numeric(10, 3), default=0)
    stock_minimo = Column(Numeric(10, 3), default=0)
    costo_unitario = Column(Numeric(10, 2), default=0)
    fecha_vencimiento = Column(Date, nullable=True)
    proveedor = Column(String(120))
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    restaurante = relationship("Restaurante", back_populates="insumos")
    proveedor_rel = relationship("Proveedor", back_populates="insumos")
    recetas = relationship("Receta", back_populates="insumo")
    desperdicios = relationship("Desperdicio", back_populates="insumo")


# ==================================================================
# 6. RECETAS (Plato ↔ Insumos)
# ==================================================================
class Receta(Base):
    __tablename__ = "recetas"

    id_receta = Column(Integer, primary_key=True, autoincrement=True)
    id_plato = Column(Integer, ForeignKey("platos.id_plato"), nullable=False)
    id_insumo = Column(Integer, ForeignKey("insumos.id_insumo"), nullable=False)
    cantidad_usada = Column(Numeric(10, 3), nullable=False)
    unidad_medida = Column(String(20))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    plato = relationship("Plato", back_populates="recetas")
    insumo = relationship("Insumo", back_populates="recetas")


# ==================================================================
# 6-B. CLIENTES
# ==================================================================
class Cliente(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, autoincrement=True)
    id_restaurante = Column(Integer, ForeignKey("restaurantes.id_restaurante"), nullable=True)
    nombre = Column(String(150), nullable=False)
    tipo_documento = Column(String(10), default="DNI")  # DNI / RUC
    numero_documento = Column(String(15), unique=True, nullable=False)
    direccion = Column(String(200), nullable=True)
    telefono = Column(String(20), nullable=True)
    correo = Column(String(120), nullable=True)
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    ventas = relationship("Venta", back_populates="cliente")


# ==================================================================
# 6-C. PROVEEDORES
# ==================================================================
class Proveedor(Base):
    __tablename__ = "proveedores"

    id_proveedor = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    tipo_documento = Column(String(10), default="RUC")  # RUC / DNI
    numero_documento = Column(String(15), unique=True, nullable=False)
    contacto = Column(String(120), nullable=True)
    telefono = Column(String(20), nullable=True)
    correo = Column(String(120), nullable=True)
    direccion = Column(String(200), nullable=True)
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    insumos = relationship("Insumo", back_populates="proveedor_rel")


# ==================================================================
# 7. VENTAS
# ==================================================================
class Venta(Base):
    __tablename__ = "ventas"

    id_venta = Column(Integer, primary_key=True, autoincrement=True)
    id_restaurante = Column(Integer, ForeignKey("restaurantes.id_restaurante"))
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=True)
    fecha = Column(Date, default=datetime.utcnow().date)
    hora = Column(String(8))  # HH:MM:SS
    total = Column(Numeric(12, 2), default=0)
    metodo_pago = Column(String(30), default="efectivo")
    tipo_comprobante = Column(String(20), default="ticket")  # ticket / boleta / factura
    numero_comprobante = Column(String(20), nullable=True)
    cliente_nombre = Column(String(150), nullable=True)
    cliente_documento = Column(String(15), nullable=True)
    observaciones = Column(Text)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    restaurante = relationship("Restaurante", back_populates="ventas")
    usuario = relationship("Usuario")
    cliente = relationship("Cliente", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")


class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"

    id_detalle = Column(Integer, primary_key=True, autoincrement=True)
    id_venta = Column(Integer, ForeignKey("ventas.id_venta"), nullable=False)
    id_plato = Column(Integer, ForeignKey("platos.id_plato"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)

    venta = relationship("Venta", back_populates="detalles")
    plato = relationship("Plato", back_populates="detalles_venta")


# ==================================================================
# 8. PRODUCCIÓN
# ==================================================================
class Produccion(Base):
    __tablename__ = "producciones"

    id_produccion = Column(Integer, primary_key=True, autoincrement=True)
    id_restaurante = Column(Integer, ForeignKey("restaurantes.id_restaurante"))
    id_plato = Column(Integer, ForeignKey("platos.id_plato"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    fecha = Column(Date, default=datetime.utcnow().date)
    cantidad_preparada = Column(Integer, nullable=False)
    cantidad_vendida = Column(Integer, default=0)
    cantidad_sobrante = Column(Integer, default=0)
    observaciones = Column(Text)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    plato = relationship("Plato", back_populates="producciones")
    usuario = relationship("Usuario")


# ==================================================================
# 9. DESPERDICIO
# ==================================================================
class Desperdicio(Base):
    __tablename__ = "desperdicios"

    id_desperdicio = Column(Integer, primary_key=True, autoincrement=True)
    id_restaurante = Column(Integer, ForeignKey("restaurantes.id_restaurante"))
    id_plato = Column(Integer, ForeignKey("platos.id_plato"), nullable=True)
    id_insumo = Column(Integer, ForeignKey("insumos.id_insumo"), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    fecha = Column(Date, default=datetime.utcnow().date)
    tipo = Column(String(20))  # plato / insumo
    cantidad = Column(Numeric(10, 3), nullable=False)
    unidad_medida = Column(String(20))
    motivo = Column(String(60), nullable=False)
    costo_estimado = Column(Numeric(10, 2), default=0)
    observaciones = Column(Text)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    plato = relationship("Plato")
    insumo = relationship("Insumo", back_populates="desperdicios")
    usuario = relationship("Usuario")


# ==================================================================
# 10. PREDICCIONES IA
# ==================================================================
class Prediccion(Base):
    __tablename__ = "predicciones"

    id_prediccion = Column(Integer, primary_key=True, autoincrement=True)
    id_restaurante = Column(Integer, ForeignKey("restaurantes.id_restaurante"))
    id_plato = Column(Integer, ForeignKey("platos.id_plato"), nullable=False)
    fecha_objetivo = Column(Date, nullable=False)
    demanda_estimada = Column(Float, nullable=False)
    recomendacion_produccion = Column(Integer, nullable=False)
    riesgo_desperdicio = Column(String(20))  # bajo / medio / alto
    modelo_usado = Column(String(50))
    mae = Column(Float)  # error absoluto medio
    r2 = Column(Float)
    confianza = Column(Float)
    fecha_generacion = Column(DateTime, default=datetime.utcnow)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))

    plato = relationship("Plato")
    usuario = relationship("Usuario")


# ==================================================================
# 11. BITÁCORA DE SUCESOS
# ==================================================================
class Bitacora(Base):
    __tablename__ = "bitacora"

    id_bitacora = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    usuario_nombre = Column(String(120))  # snapshot por seguridad
    rol = Column(String(50))
    modulo = Column(String(60), nullable=False)
    accion = Column(String(60), nullable=False)
    descripcion = Column(Text)
    fecha = Column(Date, default=datetime.utcnow().date)
    hora = Column(String(8))
    ip_equipo = Column(String(45))
    resultado = Column(String(20), default="éxito")  # éxito / error / advertencia

    usuario = relationship("Usuario", back_populates="bitacoras")


# ==================================================================
# 12. CONFIGURACIÓN
# ==================================================================
class Configuracion(Base):
    __tablename__ = "configuracion"

    id_configuracion = Column(Integer, primary_key=True, autoincrement=True)
    clave = Column(String(80), unique=True, nullable=False)
    valor = Column(String(255))
    descripcion = Column(String(255))
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================================================================
# 12-B. COMPARACIÓN DE MODELOS IA (tesis: ARIMA vs Prophet vs Transformer)
# ==================================================================
class ComparacionModelos(Base):
    __tablename__ = "comparaciones_modelos"

    id_comparacion    = Column(Integer, primary_key=True, autoincrement=True)
    id_plato          = Column(Integer, ForeignKey("platos.id_plato"), nullable=False)
    id_usuario        = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    fecha_comparacion = Column(DateTime, default=datetime.utcnow)
    modelo_ganador    = Column(String(50))
    dias_adelante     = Column(Integer)
    clima             = Column(Integer)
    evento            = Column(Integer)

    # Métricas ARIMA
    mae_arima  = Column(Float, nullable=True)
    rmse_arima = Column(Float, nullable=True)
    mape_arima = Column(Float, nullable=True)
    r2_arima   = Column(Float, nullable=True)

    # Métricas Prophet
    mae_prophet  = Column(Float, nullable=True)
    rmse_prophet = Column(Float, nullable=True)
    mape_prophet = Column(Float, nullable=True)
    r2_prophet   = Column(Float, nullable=True)

    # Métricas Transformer Híbrido
    mae_transformer  = Column(Float, nullable=True)
    rmse_transformer = Column(Float, nullable=True)
    mape_transformer = Column(Float, nullable=True)
    r2_transformer   = Column(Float, nullable=True)

    # Resultado prueba Diebold-Mariano (ganador vs mejor alternativa)
    dm_estadistico    = Column(Float, nullable=True)
    dm_p_valor        = Column(Float, nullable=True)
    dm_significativo  = Column(Boolean, nullable=True)
    dm_interpretacion = Column(String(255), nullable=True)

    plato   = relationship("Plato")
    usuario = relationship("Usuario")


# ==================================================================
# 12-C. ALERTAS INTELIGENTES — Motor interno (sin dependencia de n8n)
# ==================================================================
class AlertaInteligente(Base):
    """
    Motor interno de alertas preventivas y recomendaciones operativas.
    Reemplaza la dependencia obligatoria de n8n: las alertas se generan
    directamente desde el backend sin servicios externos.

    Tipos de alerta: RIESGO_SOBREPRODUCCION | PRODUCTO_PROXIMO_VENCER |
                     STOCK_EXCESIVO | BAJA_DEMANDA | ALTO_DESPERDICIO |
                     RECOMENDACION_MENU | ALERTA_CRITICA
    Niveles de riesgo: BAJO | MEDIO | ALTO | CRITICO
    Estados: pendiente | leida | resuelta
    """
    __tablename__ = "alertas_inteligentes"

    id_alerta        = Column(Integer, primary_key=True, autoincrement=True)
    tipo_alerta      = Column(String(50),  nullable=False)
    nivel_riesgo     = Column(String(20),  nullable=False, default="BAJO")
    titulo           = Column(String(200), nullable=False)
    descripcion      = Column(Text,        nullable=False)
    recomendacion    = Column(Text,        nullable=False)
    fecha_generacion = Column(DateTime,    default=datetime.utcnow)
    estado           = Column(String(20),  default="pendiente")   # pendiente / leida / resuelta
    id_plato         = Column(Integer, ForeignKey("platos.id_plato"),   nullable=True)
    id_insumo        = Column(Integer, ForeignKey("insumos.id_insumo"), nullable=True)
    valor_predicho   = Column(Float, nullable=True)   # demanda esperada o referencia
    valor_actual     = Column(Float, nullable=True)   # valor observado (sobrante, stock, etc.)
    porcentaje_riesgo = Column(Float, nullable=True)  # % de riesgo calculado (0-100)

    plato  = relationship("Plato")
    insumo = relationship("Insumo")


# ==================================================================
# 13. ALERTAS (auxiliar para n8n / recomendaciones)
# ==================================================================
class Alerta(Base):
    __tablename__ = "alertas"

    id_alerta = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(60))  # vencimiento / sobreproduccion / desperdicio / stock_bajo
    titulo = Column(String(150))
    mensaje = Column(Text)
    severidad = Column(String(20))  # info / advertencia / critica
    enviado_n8n = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_envio = Column(DateTime, nullable=True)
    id_restaurante = Column(Integer, ForeignKey("restaurantes.id_restaurante"), nullable=True)


# ==================================================================
# 14. EXPERIMENTACIÓN DE IA — COMPARACIÓN DE 5 MODELOS (tablas normalizadas)
# ==================================================================
# Complementan (no reemplazan) a ComparacionModelos, que sigue siendo
# usada por el endpoint original /comparar-modelos (3 modelos, ARIMA/
# Prophet/Transformer Híbrido) por compatibilidad. Estas tablas nuevas
# soportan un número arbitrario de modelos, folds de validación
# cruzada y pruebas estadísticas múltiples sin volverse rígidas.
class EjecucionEntrenamiento(Base):
    __tablename__ = "ejecuciones_entrenamiento"

    id_ejecucion = Column(Integer, primary_key=True, autoincrement=True)
    id_plato = Column(Integer, ForeignKey("platos.id_plato"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    estado = Column(String(20), default="completado")  # completado / error / en_progreso
    modelo_ganador = Column(String(50), nullable=True)
    criterio_seleccion = Column(String(120), nullable=True)
    duracion_segundos = Column(Float, nullable=True)
    numero_registros = Column(Integer, nullable=True)
    fecha_inicio_datos = Column(Date, nullable=True)
    fecha_fin_datos = Column(Date, nullable=True)
    dias_adelante = Column(Integer, nullable=True)
    clima = Column(Integer, nullable=True)
    evento = Column(Integer, nullable=True)
    ruta_artefacto = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)

    plato = relationship("Plato")
    usuario = relationship("Usuario")
    resultados_modelo = relationship(
        "ResultadoModelo", back_populates="ejecucion", cascade="all, delete-orphan"
    )
    pruebas_estadisticas = relationship(
        "ResultadoPruebaEstadistica", back_populates="ejecucion", cascade="all, delete-orphan"
    )


class ResultadoModelo(Base):
    __tablename__ = "resultados_modelo"

    id_resultado_modelo = Column(Integer, primary_key=True, autoincrement=True)
    id_ejecucion = Column(Integer, ForeignKey("ejecuciones_entrenamiento.id_ejecucion"), nullable=False)
    modelo = Column(String(50), nullable=False)
    categoria = Column(String(20), nullable=True)  # clasico / hibrido
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)
    smape = Column(Float, nullable=True)
    r2 = Column(Float, nullable=True)
    tiempo_entrenamiento = Column(Float, nullable=True)
    tiempo_inferencia = Column(Float, nullable=True)
    hiperparametros_json = Column(Text, nullable=True)
    posicion = Column(Integer, nullable=True)  # 1 = ganador
    error_mensaje = Column(String(255), nullable=True)

    ejecucion = relationship("EjecucionEntrenamiento", back_populates="resultados_modelo")
    folds = relationship("ResultadoFold", back_populates="resultado_modelo", cascade="all, delete-orphan")


class ResultadoFold(Base):
    __tablename__ = "resultados_fold"

    id_resultado_fold = Column(Integer, primary_key=True, autoincrement=True)
    id_resultado_modelo = Column(Integer, ForeignKey("resultados_modelo.id_resultado_modelo"), nullable=False)
    numero_fold = Column(Integer, nullable=False)
    fecha_inicio_train = Column(Date, nullable=True)
    fecha_fin_train = Column(Date, nullable=True)
    fecha_inicio_val = Column(Date, nullable=True)
    fecha_fin_val = Column(Date, nullable=True)
    n_train = Column(Integer, nullable=True)
    n_val = Column(Integer, nullable=True)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)
    smape = Column(Float, nullable=True)
    r2 = Column(Float, nullable=True)
    tiempo_entrenamiento = Column(Float, nullable=True)
    tiempo_inferencia = Column(Float, nullable=True)
    error_mensaje = Column(String(255), nullable=True)

    resultado_modelo = relationship("ResultadoModelo", back_populates="folds")


class ResultadoPruebaEstadistica(Base):
    __tablename__ = "resultados_prueba_estadistica"

    id_resultado_prueba = Column(Integer, primary_key=True, autoincrement=True)
    id_ejecucion = Column(Integer, ForeignKey("ejecuciones_entrenamiento.id_ejecucion"), nullable=False)
    prueba = Column(String(30), nullable=False)  # diebold_mariano / friedman / wilcoxon
    modelo_a = Column(String(50), nullable=True)
    modelo_b = Column(String(50), nullable=True)
    estadistico = Column(Float, nullable=True)
    p_valor = Column(Float, nullable=True)
    p_valor_ajustado = Column(Float, nullable=True)
    significativo = Column(Boolean, nullable=True)
    interpretacion = Column(Text, nullable=True)

    ejecucion = relationship("EjecucionEntrenamiento", back_populates="pruebas_estadisticas")


class ModeloGuardado(Base):
    __tablename__ = "modelos_guardados"

    id_modelo_guardado = Column(Integer, primary_key=True, autoincrement=True)
    id_plato = Column(Integer, ForeignKey("platos.id_plato"), nullable=False)
    id_ejecucion = Column(Integer, ForeignKey("ejecuciones_entrenamiento.id_ejecucion"), nullable=True)
    modelo = Column(String(50), nullable=False)
    ruta = Column(String(255), nullable=False)  # ruta lógica relativa (no ruta absoluta del sistema)
    fecha_entrenamiento = Column(DateTime, default=datetime.utcnow)
    hash_datos = Column(String(32), nullable=True)
    activo = Column(Boolean, default=True)
    metadata_json = Column(Text, nullable=True)

    plato = relationship("Plato")
    ejecucion = relationship("EjecucionEntrenamiento")
