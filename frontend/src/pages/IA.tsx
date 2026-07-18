import { useEffect, useState } from 'react'
import {
  Brain, Play, Loader2, Info, Zap, Trophy,
  BarChart2, AlertCircle, CheckCircle2, GitCompare, Microscope, FlaskConical,
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Legend,
} from 'recharts'
import api from '../api/client'
import EdaPanel from '../components/ia/EdaPanel'
import EntrenamientoCompleto from '../components/ia/EntrenamientoCompleto'
import ModeloGuardadoPanel from '../components/ia/ModeloGuardadoPanel'
import type { EdaResultado, EntrenarCompararResultado } from '../types/ia'

// ——— Tipos de datos ———

interface PlatoIA { id_plato: number; nombre: string; categoria: string }

interface Resultado {
  fecha: string
  demanda_estimada: number
  recomendacion: number
  riesgo: string
  mae: number
  r2: number
  confianza: number
  modelo: string
}

interface TransformerInfo {
  arquitectura: string
  n_heads: number
  d_k: number
  pesos_ensemble: Record<string, number>
  importancia_features: Record<string, number>
}

interface MetricasModelo {
  mae:  number | null
  rmse: number | null
  mape: number | null
  r2:   number | null
  error?: string
}

interface ResultadoDM {
  estadistico:    number | null
  p_valor:        number | null
  significativo:  boolean
  interpretacion: string
  modelo_1:       string
  modelo_2:       string
}

interface PrediccionFutura {
  fecha:            string
  demanda_estimada: number
  recomendacion:    number
  riesgo:           string
}

interface ComparacionResult {
  modelo_ganador:         string
  modelo_ganador_legible: string
  mae_ganador:            number
  metricas_por_modelo:    Record<string, MetricasModelo>
  info_modelos:           Record<string, Record<string, unknown>>
  diebold_mariano:        Record<string, ResultadoDM>
  predicciones_futuras:   PrediccionFutura[]
  n_datos_entrenamiento:  number
  n_datos_prueba:         number
  explicacion:            string
}

// ——— Constantes ———

const riesgoColor: Record<string, string> = {
  bajo:  'bg-green-100 text-green-700',
  medio: 'bg-yellow-100 text-yellow-700',
  alto:  'bg-red-100 text-red-700',
}

const MODELOS = [
  { value: 'random_forest',      label: 'Random Forest',      desc: 'Ensemble de árboles de decisión' },
  { value: 'regresion_lineal',   label: 'Regresión Lineal',   desc: 'Modelo lineal clásico' },
  { value: 'decision_tree',      label: 'Árbol de Decisión',  desc: 'Árbol de decisión simple' },
  {
    value: 'transformer_hibrido', label: 'Transformer Híbrido',
    desc: 'Multi-Head Attention + Ensemble (RF + GBR + LR + DT) + Ridge Meta-Learner',
    advanced: true,
  },
]

const CLIMAS  = [
  { value: 1, label: '☀️ Soleado' },
  { value: 2, label: '⛅ Nublado' },
  { value: 3, label: '🌧️ Lluvia'  },
]

const EVENTOS = [
  { value: 0, label: 'Normal'      },
  { value: 1, label: 'Evento local' },
  { value: 2, label: 'Feriado'     },
]

const NOMBRES_MODELOS: Record<string, string> = {
  arima:              'ARIMA',
  prophet:            'Prophet',
  transformer_hibrido: 'Transformer Híbrido',
}

// ——— Componente principal ———

export default function IA() {
  // Estado — predicción individual
  const [platos, setPlatos]               = useState<PlatoIA[]>([])
  const [idPlato, setIdPlato]             = useState(0)
  const [dias, setDias]                   = useState(7)
  const [modelo, setModelo]               = useState('random_forest')
  const [clima, setClima]                 = useState(2)
  const [evento, setEvento]               = useState(0)
  const [nHeads, setNHeads]               = useState(4)
  const [dK, setDK]                       = useState(16)
  const [loading, setLoading]             = useState(false)
  const [resultados, setResultados]       = useState<Resultado[]>([])
  const [transformerInfo, setTransformerInfo] = useState<TransformerInfo | null>(null)
  const [metricas, setMetricas]           = useState<{ mae?: number; r2?: number; modelo?: string }>({})
  const [error, setError]                 = useState('')
  const [tiempoMs, setTiempoMs]           = useState<number | null>(null)

  // Estado — comparación automática
  const [loadingComp, setLoadingComp]     = useState(false)
  const [comparacion, setComparacion]     = useState<ComparacionResult | null>(null)
  const [errorComp, setErrorComp]         = useState('')
  const [tiempoCompMs, setTiempoCompMs]   = useState<number | null>(null)

  // Estado — análisis exploratorio de datos (EDA)
  const [loadingEda, setLoadingEda]       = useState(false)
  const [eda, setEda]                     = useState<EdaResultado | null>(null)
  const [errorEda, setErrorEda]           = useState('')

  // Estado — entrenamiento completo (5 modelos + CV + tuning + pruebas estadísticas)
  const [loadingCompleto, setLoadingCompleto] = useState(false)
  const [entrenamientoCompleto, setEntrenamientoCompleto] = useState<EntrenarCompararResultado | null>(null)
  const [errorCompleto, setErrorCompleto] = useState('')

  useEffect(() => {
    api.get('/ia/platos-disponibles').then((r) => setPlatos(r.data))
  }, [])

  // ——— Predicción individual ———
  const ejecutar = async () => {
    if (!idPlato) return setError('Selecciona un plato')
    setLoading(true)
    setError('')
    setResultados([])
    setTransformerInfo(null)
    const t0 = Date.now()

    try {
      const payload: Record<string, unknown> = {
        id_plato:     idPlato,
        dias_adelante: dias,
        modelo_tipo:  modelo,
        clima,
        evento,
      }
      if (modelo === 'transformer_hibrido') {
        payload.n_heads = nHeads
        payload.d_k     = dK
      }

      const r = await api.post('/ia/predecir', payload)
      setResultados(r.data.resultados)
      setMetricas({ mae: r.data.mae, r2: r.data.r2, modelo: r.data.modelo_tipo })
      setTransformerInfo(r.data.transformer_info ?? null)
      setTiempoMs(Date.now() - t0)
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error en predicción')
    } finally {
      setLoading(false)
    }
  }

  // ——— Comparación automática de modelos ———
  const ejecutarComparacion = async () => {
    if (!idPlato) return setErrorComp('Selecciona un plato')
    setLoadingComp(true)
    setErrorComp('')
    setComparacion(null)
    const t0 = Date.now()

    try {
      const r = await api.post('/ia/comparar-modelos', {
        id_plato:     idPlato,
        dias_adelante: dias,
        clima,
        evento,
      })
      setComparacion(r.data)
      setTiempoCompMs(Date.now() - t0)
    } catch (e: unknown) {
      setErrorComp(
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Error en la comparación de modelos'
      )
    } finally {
      setLoadingComp(false)
    }
  }

  // ——— Análisis exploratorio de datos (EDA) ———
  const ejecutarEda = async () => {
    if (!idPlato) return setErrorEda('Selecciona un plato')
    setLoadingEda(true)
    setErrorEda('')
    setEda(null)

    try {
      const r = await api.get(`/ia/eda/${idPlato}`)
      setEda(r.data)
    } catch (e: unknown) {
      setErrorEda(
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Error al generar el análisis exploratorio de datos'
      )
    } finally {
      setLoadingEda(false)
    }
  }

  // ——— Entrenamiento completo (5 modelos + CV + tuning + pruebas estadísticas) ———
  const ejecutarEntrenamientoCompleto = async () => {
    if (!idPlato) return setErrorCompleto('Selecciona un plato')
    setLoadingCompleto(true)
    setErrorCompleto('')
    setEntrenamientoCompleto(null)

    try {
      const r = await api.post('/ia/entrenar-comparar', {
        id_plato: idPlato,
        dias_adelante: dias,
        clima,
        evento,
        n_splits: 5,
        ejecutar_tuning: true,
        guardar_ganador: true,
      })
      setEntrenamientoCompleto(r.data)
    } catch (e: unknown) {
      setErrorCompleto(
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Error en el entrenamiento completo'
      )
    } finally {
      setLoadingCompleto(false)
    }
  }

  const isTransformer = modelo === 'transformer_hibrido'

  // Datos para gráfico de pesos del Transformer
  const ensembleData = transformerInfo
    ? Object.entries(transformerInfo.pesos_ensemble).map(([name, weight]) => ({
        name,
        peso: parseFloat(Math.abs(weight).toFixed(4)),
        raw:  weight,
      }))
    : []

  // Datos para radar de importancia de features
  const featureData = transformerInfo
    ? Object.entries(transformerInfo.importancia_features).map(([name, imp]) => ({
        feature:     name,
        importancia: parseFloat((imp * 100).toFixed(2)),
      }))
    : []

  // Helper para formatear métricas
  const fmt = (v: number | null | undefined, dec = 4) =>
    v === null || v === undefined ? '—' : v.toFixed(dec)

  // Orden fijo para la tabla comparativa
  const ORDEN_MODELOS = ['arima', 'prophet', 'transformer_hibrido'] as const

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Brain className="w-7 h-7 text-primary-600" /> IA / Predicciones
        </h1>
        <p className="text-sm text-gray-500">
          Predicción de demanda con Machine Learning — Comparación automática de modelos
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* ═══════════════════════════════════════════════════
            PANEL IZQUIERDO — PARÁMETROS
        ═══════════════════════════════════════════════════ */}
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-base font-semibold text-gray-700 mb-4">Parámetros</h2>
            <div className="space-y-3">

              {/* Selector de plato */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Plato *</label>
                <select
                  value={idPlato}
                  onChange={(e) => setIdPlato(+e.target.value)}
                  className="input-field"
                >
                  <option value={0}>Seleccionar...</option>
                  {platos.map((p) => (
                    <option key={p.id_plato} value={p.id_plato}>{p.nombre}</option>
                  ))}
                </select>
              </div>

              {/* Selector de modelo (solo para predicción individual) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Modelo (predicción individual)
                </label>
                <div className="space-y-2">
                  {MODELOS.map((m) => (
                    <label
                      key={m.value}
                      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        modelo === m.value
                          ? 'border-primary-400 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        value={m.value}
                        checked={modelo === m.value}
                        onChange={() => setModelo(m.value)}
                        className="mt-0.5 accent-primary-600"
                      />
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm font-medium text-gray-800">{m.label}</span>
                          {m.advanced && (
                            <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded-full font-medium flex items-center gap-0.5">
                              <Zap className="w-3 h-3" /> Avanzado
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">{m.desc}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Días / Clima / Evento */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Días a predecir</label>
                  <input
                    type="number" min={1} max={30} value={dias}
                    onChange={(e) => setDias(+e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Clima</label>
                  <select value={clima} onChange={(e) => setClima(+e.target.value)} className="input-field">
                    {CLIMAS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Evento</label>
                  <select value={evento} onChange={(e) => setEvento(+e.target.value)} className="input-field">
                    {EVENTOS.map((ev) => <option key={ev.value} value={ev.value}>{ev.label}</option>)}
                  </select>
                </div>
              </div>

              {/* Hiperparámetros del Transformer (solo predicción individual) */}
              {isTransformer && (
                <div className="bg-purple-50 border border-purple-200 rounded-xl p-3">
                  <p className="text-xs font-semibold text-purple-700 mb-2 flex items-center gap-1">
                    <Zap className="w-3.5 h-3.5" /> Hiperparámetros Transformer
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Cabezas atención</label>
                      <select value={nHeads} onChange={(e) => setNHeads(+e.target.value)} className="input-field text-sm">
                        {[1, 2, 4, 8].map((n) => <option key={n} value={n}>{n}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">d_k (dim. clave)</label>
                      <select value={dK} onChange={(e) => setDK(+e.target.value)} className="input-field text-sm">
                        {[4, 8, 16, 32, 64].map((d) => <option key={d} value={d}>{d}</option>)}
                      </select>
                    </div>
                  </div>
                  <p className="text-xs text-purple-600 mt-2">
                    {nHeads} cabezas × d_k={dK} → {nHeads * dK} dimensiones de atención
                  </p>
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
                </div>
              )}

              {/* Botón — predicción individual */}
              <button
                onClick={ejecutar}
                disabled={loading || !idPlato}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {loading ? 'Calculando...' : 'Ejecutar Predicción'}
              </button>

              {/* Separador — EDA */}
              <div className="border-t border-dashed border-gray-200 pt-3">
                <p className="text-xs text-gray-500 mb-2 font-medium flex items-center gap-1">
                  <Microscope className="w-3.5 h-3.5" />
                  Análisis exploratorio de datos
                </p>
                <p className="text-xs text-gray-400 mb-2">
                  Estadísticas descriptivas, calidad de datos, distribución,
                  estacionalidad y correlaciones del histórico del plato.
                </p>

                {errorEda && (
                  <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700 flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" /> {errorEda}
                  </div>
                )}

                <button
                  onClick={ejecutarEda}
                  disabled={loadingEda || !idPlato}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg
                             bg-teal-600 hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed
                             text-white text-sm font-medium transition-colors"
                >
                  {loadingEda
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Analizando datos...</>
                    : <><Microscope className="w-4 h-4" /> Analizar datos (EDA)</>
                  }
                </button>
              </div>

              {/* Separador — comparación automática */}
              <div className="border-t border-dashed border-gray-200 pt-3">
                <p className="text-xs text-gray-500 mb-2 font-medium flex items-center gap-1">
                  <GitCompare className="w-3.5 h-3.5" />
                  Comparación automática (tesis)
                </p>
                <p className="text-xs text-gray-400 mb-2">
                  Compara ARIMA, Prophet y Transformer con hiperparámetros
                  seleccionados automáticamente. Solo elige plato, días, clima y evento.
                </p>

                {errorComp && (
                  <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700 flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" /> {errorComp}
                  </div>
                )}

                {/* Botón — comparación automática */}
                <button
                  onClick={ejecutarComparacion}
                  disabled={loadingComp || !idPlato}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg
                             bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed
                             text-white text-sm font-medium transition-colors"
                >
                  {loadingComp
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Comparando modelos...</>
                    : <><GitCompare className="w-4 h-4" /> Comparar modelos automáticamente</>
                  }
                </button>
              </div>

              {/* Separador — entrenamiento completo (5 modelos) */}
              <div className="border-t border-dashed border-gray-200 pt-3">
                <p className="text-xs text-gray-500 mb-2 font-medium flex items-center gap-1">
                  <FlaskConical className="w-3.5 h-3.5" />
                  Experimentación completa (5 modelos)
                </p>
                <p className="text-xs text-gray-400 mb-2">
                  ARIMA, Prophet, Holt-Winters, Transformer+RF y Transformer+GBR con
                  validación cruzada, optimización de hiperparámetros y pruebas
                  estadísticas (Friedman, Wilcoxon, Diebold-Mariano). Puede tardar
                  varias decenas de segundos.
                </p>

                {errorCompleto && (
                  <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700 flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" /> {errorCompleto}
                  </div>
                )}

                <button
                  onClick={ejecutarEntrenamientoCompleto}
                  disabled={loadingCompleto || !idPlato}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg
                             bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed
                             text-white text-sm font-medium transition-colors"
                >
                  {loadingCompleto
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Entrenando (puede tardar)...</>
                    : <><FlaskConical className="w-4 h-4" /> Ejecutar experimentación completa</>
                  }
                </button>
              </div>

              {idPlato > 0 && (
                <ModeloGuardadoPanel idPlato={idPlato} diasAdelante={dias} clima={clima} evento={evento} />
              )}
            </div>
          </div>

          {/* Métricas de la predicción individual */}
          {metricas.mae !== undefined && (
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Métricas del modelo</h3>
              <div className="grid grid-cols-2 gap-2 mb-2">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500">MAE</p>
                  <p className="text-xl font-bold text-gray-800">{metricas.mae?.toFixed(3)}</p>
                  <p className="text-xs text-gray-400">Error Absoluto Medio</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500">R²</p>
                  <p className="text-xl font-bold text-gray-800">{metricas.r2?.toFixed(3)}</p>
                  <p className="text-xs text-gray-400">Bondad de ajuste</p>
                </div>
              </div>
              {tiempoMs && (
                <p className="text-xs text-gray-400 text-center">Tiempo de cómputo: {tiempoMs} ms</p>
              )}
            </div>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════
            PANEL DERECHO — RESULTADOS
        ═══════════════════════════════════════════════════ */}
        <div className="xl:col-span-2 space-y-4">

          {/* Estado vacío */}
          {resultados.length === 0 && !comparacion && !eda && !entrenamientoCompleto &&
           !loading && !loadingComp && !loadingEda && !loadingCompleto && (
            <div className="card flex flex-col items-center justify-center py-16 text-center">
              <Brain className="w-16 h-16 text-gray-200 mb-4" />
              <p className="text-gray-500">Selecciona un plato y ejecuta una predicción</p>
              <p className="text-sm text-gray-400 mt-1">
                El sistema requiere al menos 10 registros históricos para predicción
                individual y 30 para comparación de modelos.
              </p>
            </div>
          )}

          {/* Estado de carga — EDA */}
          {loadingEda && (
            <div className="card flex flex-col items-center justify-center py-16 text-center">
              <Loader2 className="w-10 h-10 text-teal-500 animate-spin mb-3" />
              <p className="text-gray-500">Generando análisis exploratorio de datos...</p>
            </div>
          )}

          {/* Estado de carga — entrenamiento completo */}
          {loadingCompleto && (
            <div className="card flex flex-col items-center justify-center py-16 text-center">
              <Loader2 className="w-10 h-10 text-purple-500 animate-spin mb-3" />
              <p className="text-gray-500">Ejecutando experimentación completa...</p>
              <p className="text-xs text-gray-400 mt-1">
                5 modelos, validación cruzada, tuning y pruebas estadísticas — puede tardar varias decenas de segundos.
              </p>
            </div>
          )}

          {/* ─────────────────────────────────────────
              SECCIÓN — ENTRENAMIENTO COMPLETO (5 MODELOS)
          ───────────────────────────────────────── */}
          {entrenamientoCompleto && !loadingCompleto && (
            <EntrenamientoCompleto data={entrenamientoCompleto} />
          )}

          {/* ─────────────────────────────────────────
              SECCIÓN — ANÁLISIS EXPLORATORIO DE DATOS (EDA)
          ───────────────────────────────────────── */}
          {eda && !loadingEda && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Microscope className="w-5 h-5 text-teal-600" />
                <h2 className="text-base font-bold text-gray-800">
                  Análisis Exploratorio de Datos — {eda.resumen.plato}
                </h2>
              </div>
              <EdaPanel data={eda} />
            </div>
          )}

          {/* ─────────────────────────────────────────
              SECCIÓN A — PREDICCIÓN INDIVIDUAL
          ───────────────────────────────────────── */}
          {resultados.length > 0 && (
            <>
              {/* Gráfico demanda */}
              <div className="card">
                <h2 className="text-base font-semibold text-gray-700 mb-4">
                  Demanda estimada vs. producción recomendada
                </h2>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={resultados}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="fecha" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone" dataKey="demanda_estimada"
                      stroke="#6366f1" strokeWidth={2.5} name="Demanda estimada" dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone" dataKey="recomendacion"
                      stroke="#f59e0b" strokeWidth={2} strokeDasharray="6 3"
                      name="Producción recomendada" dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Tabla de detalle */}
              <div className="card">
                <h2 className="text-base font-semibold text-gray-700 mb-3">Detalle por día</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Fecha</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">Demanda</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">Producción rec.</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">Confianza</th>
                        <th className="px-3 py-2 text-xs font-semibold text-gray-500">Riesgo</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {resultados.map((r) => (
                        <tr key={r.fecha} className="hover:bg-gray-50">
                          <td className="px-3 py-2.5 font-medium">{r.fecha}</td>
                          <td className="px-3 py-2.5 text-right font-semibold text-primary-700">{r.demanda_estimada}</td>
                          <td className="px-3 py-2.5 text-right">{r.recomendacion}</td>
                          <td className="px-3 py-2.5 text-right">{(r.confianza * 100).toFixed(1)}%</td>
                          <td className="px-3 py-2.5">
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riesgoColor[r.riesgo]}`}>
                              {r.riesgo}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Info exclusiva del Transformer Híbrido */}
              {transformerInfo && (
                <>
                  <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <Zap className="w-4 h-4 text-purple-600" />
                      <h2 className="text-sm font-bold text-purple-800">Transformer Híbrido — Arquitectura</h2>
                    </div>
                    <p className="text-xs text-purple-600 font-mono">{transformerInfo.arquitectura}</p>
                    <div className="flex gap-4 mt-2 text-xs text-purple-600">
                      <span>Cabezas: <strong>{transformerInfo.n_heads}</strong></span>
                      <span>d_k: <strong>{transformerInfo.d_k}</strong></span>
                      <span>Dim. total: <strong>{transformerInfo.n_heads * transformerInfo.d_k}</strong></span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="card">
                      <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1">
                        <Info className="w-4 h-4 text-gray-400" /> Pesos del Meta-Learner (Ridge)
                      </h2>
                      <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={ensembleData} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                          <XAxis type="number" tick={{ fontSize: 10 }} />
                          <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={110} />
                          <Tooltip formatter={(v) => [Number(v).toFixed(4), 'Peso']} />
                          <Bar dataKey="peso" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {featureData.length > 0 && (
                      <div className="card">
                        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1">
                          <Info className="w-4 h-4 text-gray-400" /> Importancia de features (RF interno)
                        </h2>
                        <ResponsiveContainer width="100%" height={180}>
                          <RadarChart data={featureData}>
                            <PolarGrid />
                            <PolarAngleAxis dataKey="feature" tick={{ fontSize: 9 }} />
                            <PolarRadiusAxis angle={30} tick={{ fontSize: 8 }} />
                            <Radar name="Importancia" dataKey="importancia" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
                            <Tooltip formatter={(v) => [`${v}%`, 'Importancia']} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                </>
              )}
            </>
          )}

          {/* ─────────────────────────────────────────
              SECCIÓN B — COMPARACIÓN AUTOMÁTICA DE MODELOS
          ───────────────────────────────────────── */}
          {comparacion && (
            <div className="space-y-4">

              {/* Encabezado y modelo ganador */}
              <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-4">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div>
                    <h2 className="text-base font-bold text-indigo-800 flex items-center gap-2">
                      <GitCompare className="w-5 h-5" />
                      Comparación Automática de Modelos
                    </h2>
                    <p className="text-xs text-indigo-600 mt-0.5">
                      {comparacion.n_datos_entrenamiento} días de entrenamiento /&nbsp;
                      {comparacion.n_datos_prueba} días de prueba (split cronológico)
                    </p>
                  </div>
                  <div className="flex items-center gap-2 bg-white border border-indigo-300 rounded-lg px-3 py-2 shadow-sm">
                    <Trophy className="w-5 h-5 text-yellow-500" />
                    <div>
                      <p className="text-xs text-gray-500">Modelo ganador</p>
                      <p className="text-sm font-bold text-indigo-700">
                        {comparacion.modelo_ganador_legible}
                      </p>
                      <p className="text-xs text-gray-400">MAE = {comparacion.mae_ganador}</p>
                    </div>
                  </div>
                </div>
                {tiempoCompMs && (
                  <p className="text-xs text-indigo-400 mt-2">Tiempo de cómputo: {tiempoCompMs} ms</p>
                )}
              </div>

              {/* Tabla comparativa de métricas */}
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-indigo-500" />
                  Métricas de error por modelo
                  <span className="text-xs font-normal text-gray-400 ml-1">
                    (valores menores → mayor precisión)
                  </span>
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left px-3 py-2 text-xs font-semibold text-gray-600">Modelo</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">MAE</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">RMSE</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">MAPE (%)</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">R²</th>
                        <th className="text-center px-3 py-2 text-xs font-semibold text-gray-600">Estado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {ORDEN_MODELOS.map((key) => {
                        const m = comparacion.metricas_por_modelo[key]
                        const esGanador = key === comparacion.modelo_ganador
                        if (!m) return null
                        return (
                          <tr
                            key={key}
                            className={esGanador
                              ? 'bg-indigo-50 font-semibold'
                              : 'hover:bg-gray-50'
                            }
                          >
                            <td className="px-3 py-2.5 flex items-center gap-2">
                              {esGanador && <Trophy className="w-4 h-4 text-yellow-500 flex-shrink-0" />}
                              <span className={esGanador ? 'text-indigo-700' : 'text-gray-700'}>
                                {NOMBRES_MODELOS[key] || key}
                              </span>
                            </td>
                            <td className={`px-3 py-2.5 text-right font-mono ${esGanador ? 'text-indigo-700' : ''}`}>
                              {fmt(m.mae)}
                            </td>
                            <td className="px-3 py-2.5 text-right font-mono">{fmt(m.rmse)}</td>
                            <td className="px-3 py-2.5 text-right font-mono">
                              {m.mape !== null && m.mape !== undefined ? fmt(m.mape, 2) : '—'}
                            </td>
                            <td className="px-3 py-2.5 text-right font-mono">
                              {m.r2 !== null && m.r2 !== undefined ? fmt(m.r2, 4) : '—'}
                            </td>
                            <td className="px-3 py-2.5 text-center">
                              {m.error ? (
                                <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">
                                  Error
                                </span>
                              ) : esGanador ? (
                                <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium flex items-center gap-0.5 justify-center">
                                  <CheckCircle2 className="w-3 h-3" /> Ganador
                                </span>
                              ) : (
                                <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                                  Evaluado
                                </span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Prueba Diebold-Mariano */}
              {Object.keys(comparacion.diebold_mariano).length > 0 && (
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">
                    Prueba Diebold-Mariano — Validación estadística
                    <span className="text-xs font-normal text-gray-400 ml-2">
                      H₀: igualdad de precisión predictiva
                    </span>
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(comparacion.diebold_mariano).map(([clave, dm]) => (
                      <div
                        key={clave}
                        className={`rounded-lg border p-3 ${
                          dm.significativo
                            ? 'border-green-200 bg-green-50'
                            : 'border-gray-200 bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2 flex-wrap">
                          <div>
                            <p className="text-xs font-semibold text-gray-700">
                              {dm.modelo_1} vs {dm.modelo_2}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">{dm.interpretacion}</p>
                          </div>
                          <div className="flex gap-3 text-xs text-right">
                            <div>
                              <p className="text-gray-400">Estadístico DM</p>
                              <p className="font-mono font-semibold text-gray-700">
                                {dm.estadistico !== null ? dm.estadistico : '—'}
                              </p>
                            </div>
                            <div>
                              <p className="text-gray-400">p-valor</p>
                              <p className={`font-mono font-semibold ${
                                dm.significativo ? 'text-green-700' : 'text-gray-700'
                              }`}>
                                {dm.p_valor !== null ? dm.p_valor : '—'}
                              </p>
                            </div>
                            <div>
                              <p className="text-gray-400">Significativo</p>
                              <p className={`font-semibold ${dm.significativo ? 'text-green-600' : 'text-gray-500'}`}>
                                {dm.significativo ? 'Sí (p < 0.05)' : 'No'}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Gráfico de predicciones futuras */}
              {comparacion.predicciones_futuras.length > 0 && (
                <div className="card">
                  <h2 className="text-base font-semibold text-gray-700 mb-1">
                    Predicciones futuras — {comparacion.modelo_ganador_legible}
                  </h2>
                  <p className="text-xs text-gray-400 mb-4">
                    Generadas con el modelo ganador usando hiperparámetros automáticos
                  </p>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={comparacion.predicciones_futuras}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="fecha" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone" dataKey="demanda_estimada"
                        stroke="#6366f1" strokeWidth={2.5} name="Demanda estimada" dot={{ r: 4 }}
                      />
                      <Line
                        type="monotone" dataKey="recomendacion"
                        stroke="#f59e0b" strokeWidth={2} strokeDasharray="6 3"
                        name="Producción recomendada" dot={{ r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>

                  {/* Tabla de predicciones futuras */}
                  <div className="overflow-x-auto mt-4">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-gray-50">
                          <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Fecha</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">Demanda est.</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">Prod. recomendada</th>
                          <th className="px-3 py-2 text-xs font-semibold text-gray-500">Riesgo desperdicio</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {comparacion.predicciones_futuras.map((p) => (
                          <tr key={p.fecha} className="hover:bg-gray-50">
                            <td className="px-3 py-2.5 font-medium">{p.fecha}</td>
                            <td className="px-3 py-2.5 text-right font-semibold text-indigo-700">
                              {p.demanda_estimada}
                            </td>
                            <td className="px-3 py-2.5 text-right">{p.recomendacion}</td>
                            <td className="px-3 py-2.5">
                              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riesgoColor[p.riesgo]}`}>
                                {p.riesgo}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Explicación para la tesis */}
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-blue-800 mb-1">
                      Interpretación del resultado
                    </h4>
                    <p className="text-xs text-blue-700 leading-relaxed">
                      {comparacion.explicacion}
                    </p>
                    <p className="text-xs text-blue-600 mt-2 font-medium">
                      El modelo seleccionado presenta el menor error promedio, por lo tanto,
                      se considera el más adecuado para la predicción del desperdicio alimentario.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
