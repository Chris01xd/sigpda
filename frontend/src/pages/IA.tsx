import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
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

// Claves de los modelos disponibles para predicción individual (los textos
// visibles se resuelven vía i18n dentro del componente)
const MODELOS_KEYS = [
  { value: 'random_forest' },
  { value: 'regresion_lineal' },
  { value: 'decision_tree' },
  { value: 'transformer_hibrido', advanced: true },
]

const CLIMAS_KEYS  = [
  { value: 1, key: 'soleado' },
  { value: 2, key: 'nublado' },
  { value: 3, key: 'lluvia'  },
]

const EVENTOS_KEYS = [
  { value: 0, key: 'normal'      },
  { value: 1, key: 'evento_local' },
  { value: 2, key: 'feriado'     },
]

// ——— Componente principal ———

export default function IA() {
  const { t } = useTranslation('ia')

  // Modelos, climas y eventos con sus textos traducidos
  const MODELOS = MODELOS_KEYS.map((m) => ({
    ...m,
    label: t(`parametros.modelos.${m.value}.label`),
    desc:  t(`parametros.modelos.${m.value}.desc`),
  }))
  const CLIMAS  = CLIMAS_KEYS.map((c) => ({ ...c, label: t(`parametros.climas.${c.key}`) }))
  const EVENTOS = EVENTOS_KEYS.map((ev) => ({ ...ev, label: t(`parametros.eventos.${ev.key}`) }))
  const NOMBRES_MODELOS: Record<string, string> = {
    arima:               t('comparacion.nombres_modelos.arima'),
    prophet:             t('comparacion.nombres_modelos.prophet'),
    transformer_hibrido: t('comparacion.nombres_modelos.transformer_hibrido'),
  }

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
    if (!idPlato) return setError(t('errores.seleccionar_plato'))
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
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('errores.prediccion'))
    } finally {
      setLoading(false)
    }
  }

  // ——— Comparación automática de modelos ———
  const ejecutarComparacion = async () => {
    if (!idPlato) return setErrorComp(t('errores.seleccionar_plato'))
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
        t('errores.comparacion')
      )
    } finally {
      setLoadingComp(false)
    }
  }

  // ——— Análisis exploratorio de datos (EDA) ———
  const ejecutarEda = async () => {
    if (!idPlato) return setErrorEda(t('errores.seleccionar_plato'))
    setLoadingEda(true)
    setErrorEda('')
    setEda(null)

    try {
      const r = await api.get(`/ia/eda/${idPlato}`)
      setEda(r.data)
    } catch (e: unknown) {
      setErrorEda(
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        t('errores.eda')
      )
    } finally {
      setLoadingEda(false)
    }
  }

  // ——— Entrenamiento completo (5 modelos + CV + tuning + pruebas estadísticas) ———
  const ejecutarEntrenamientoCompleto = async () => {
    if (!idPlato) return setErrorCompleto(t('errores.seleccionar_plato'))
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
        t('errores.entrenamiento_completo')
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
          <Brain className="w-7 h-7 text-primary-600" /> {t('titulo')}
        </h1>
        <p className="text-sm text-gray-500">
          {t('subtitulo')}
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* ═══════════════════════════════════════════════════
            PANEL IZQUIERDO — PARÁMETROS
        ═══════════════════════════════════════════════════ */}
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-base font-semibold text-gray-700 mb-4">{t('parametros.titulo')}</h2>
            <div className="space-y-3">

              {/* Selector de plato */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('parametros.plato_label')}</label>
                <select
                  value={idPlato}
                  onChange={(e) => setIdPlato(+e.target.value)}
                  className="input-field"
                >
                  <option value={0}>{t('parametros.seleccionar')}</option>
                  {platos.map((p) => (
                    <option key={p.id_plato} value={p.id_plato}>{p.nombre}</option>
                  ))}
                </select>
              </div>

              {/* Selector de modelo (solo para predicción individual) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('parametros.modelo_label')}
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
                              <Zap className="w-3 h-3" /> {t('parametros.avanzado')}
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
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('parametros.dias_label')}</label>
                  <input
                    type="number" min={1} max={30} value={dias}
                    onChange={(e) => setDias(+e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('parametros.clima_label')}</label>
                  <select value={clima} onChange={(e) => setClima(+e.target.value)} className="input-field">
                    {CLIMAS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('parametros.evento_label')}</label>
                  <select value={evento} onChange={(e) => setEvento(+e.target.value)} className="input-field">
                    {EVENTOS.map((ev) => <option key={ev.value} value={ev.value}>{ev.label}</option>)}
                  </select>
                </div>
              </div>

              {/* Hiperparámetros del Transformer (solo predicción individual) */}
              {isTransformer && (
                <div className="bg-purple-50 border border-purple-200 rounded-xl p-3">
                  <p className="text-xs font-semibold text-purple-700 mb-2 flex items-center gap-1">
                    <Zap className="w-3.5 h-3.5" /> {t('parametros.transformer.titulo')}
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">{t('parametros.transformer.cabezas_label')}</label>
                      <select value={nHeads} onChange={(e) => setNHeads(+e.target.value)} className="input-field text-sm">
                        {[1, 2, 4, 8].map((n) => <option key={n} value={n}>{n}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">{t('parametros.transformer.dk_label')}</label>
                      <select value={dK} onChange={(e) => setDK(+e.target.value)} className="input-field text-sm">
                        {[4, 8, 16, 32, 64].map((d) => <option key={d} value={d}>{d}</option>)}
                      </select>
                    </div>
                  </div>
                  <p className="text-xs text-purple-600 mt-2">
                    {t('parametros.transformer.resumen', { nHeads, dK, total: nHeads * dK })}
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
                {loading ? t('parametros.boton_calculando') : t('parametros.boton_ejecutar')}
              </button>

              {/* Separador — EDA */}
              <div className="border-t border-dashed border-gray-200 pt-3">
                <p className="text-xs text-gray-500 mb-2 font-medium flex items-center gap-1">
                  <Microscope className="w-3.5 h-3.5" />
                  {t('eda_seccion.titulo')}
                </p>
                <p className="text-xs text-gray-400 mb-2">
                  {t('eda_seccion.descripcion')}
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
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('eda_seccion.boton_cargando')}</>
                    : <><Microscope className="w-4 h-4" /> {t('eda_seccion.boton')}</>
                  }
                </button>
              </div>

              {/* Separador — comparación automática */}
              <div className="border-t border-dashed border-gray-200 pt-3">
                <p className="text-xs text-gray-500 mb-2 font-medium flex items-center gap-1">
                  <GitCompare className="w-3.5 h-3.5" />
                  {t('comparacion_seccion.titulo')}
                </p>
                <p className="text-xs text-gray-400 mb-2">
                  {t('comparacion_seccion.descripcion')}
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
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('comparacion_seccion.boton_cargando')}</>
                    : <><GitCompare className="w-4 h-4" /> {t('comparacion_seccion.boton')}</>
                  }
                </button>
              </div>

              {/* Separador — entrenamiento completo (5 modelos) */}
              <div className="border-t border-dashed border-gray-200 pt-3">
                <p className="text-xs text-gray-500 mb-2 font-medium flex items-center gap-1">
                  <FlaskConical className="w-3.5 h-3.5" />
                  {t('entrenamiento_seccion.titulo')}
                </p>
                <p className="text-xs text-gray-400 mb-2">
                  {t('entrenamiento_seccion.descripcion')}
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
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('entrenamiento_seccion.boton_cargando')}</>
                    : <><FlaskConical className="w-4 h-4" /> {t('entrenamiento_seccion.boton')}</>
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
              <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('metricas_individuales.titulo')}</h3>
              <div className="grid grid-cols-2 gap-2 mb-2">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500">MAE</p>
                  <p className="text-xl font-bold text-gray-800">{metricas.mae?.toFixed(3)}</p>
                  <p className="text-xs text-gray-400">{t('metricas_individuales.mae_desc')}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500">R²</p>
                  <p className="text-xl font-bold text-gray-800">{metricas.r2?.toFixed(3)}</p>
                  <p className="text-xs text-gray-400">{t('metricas_individuales.r2_desc')}</p>
                </div>
              </div>
              {tiempoMs && (
                <p className="text-xs text-gray-400 text-center">{t('tiempo_computo', { ms: tiempoMs })}</p>
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
              <p className="text-gray-500">{t('estado_vacio.titulo')}</p>
              <p className="text-sm text-gray-400 mt-1">
                {t('estado_vacio.descripcion')}
              </p>
            </div>
          )}

          {/* Estado de carga — EDA */}
          {loadingEda && (
            <div className="card flex flex-col items-center justify-center py-16 text-center">
              <Loader2 className="w-10 h-10 text-teal-500 animate-spin mb-3" />
              <p className="text-gray-500">{t('eda_seccion.cargando_resultado')}</p>
            </div>
          )}

          {/* Estado de carga — entrenamiento completo */}
          {loadingCompleto && (
            <div className="card flex flex-col items-center justify-center py-16 text-center">
              <Loader2 className="w-10 h-10 text-purple-500 animate-spin mb-3" />
              <p className="text-gray-500">{t('entrenamiento_seccion.cargando_resultado')}</p>
              <p className="text-xs text-gray-400 mt-1">
                {t('entrenamiento_seccion.cargando_detalle')}
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
                  {t('eda_seccion.encabezado', { plato: eda.resumen.plato })}
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
                  {t('prediccion.grafico_titulo')}
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
                      stroke="#6366f1" strokeWidth={2.5} name={t('prediccion.serie_demanda')} dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone" dataKey="recomendacion"
                      stroke="#f59e0b" strokeWidth={2} strokeDasharray="6 3"
                      name={t('prediccion.serie_produccion')} dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Tabla de detalle */}
              <div className="card">
                <h2 className="text-base font-semibold text-gray-700 mb-3">{t('prediccion.tabla_titulo')}</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">{t('prediccion.columnas.fecha')}</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">{t('prediccion.columnas.demanda')}</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">{t('prediccion.columnas.produccion_rec')}</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">{t('prediccion.columnas.confianza')}</th>
                        <th className="px-3 py-2 text-xs font-semibold text-gray-500">{t('prediccion.columnas.riesgo')}</th>
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
                      <h2 className="text-sm font-bold text-purple-800">{t('prediccion.transformer.titulo')}</h2>
                    </div>
                    <p className="text-xs text-purple-600 font-mono">{transformerInfo.arquitectura}</p>
                    <div className="flex gap-4 mt-2 text-xs text-purple-600">
                      <span>{t('prediccion.transformer.cabezas')} <strong>{transformerInfo.n_heads}</strong></span>
                      <span>{t('prediccion.transformer.dk')} <strong>{transformerInfo.d_k}</strong></span>
                      <span>{t('prediccion.transformer.dim_total')} <strong>{transformerInfo.n_heads * transformerInfo.d_k}</strong></span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="card">
                      <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1">
                        <Info className="w-4 h-4 text-gray-400" /> {t('prediccion.transformer.pesos_titulo')}
                      </h2>
                      <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={ensembleData} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                          <XAxis type="number" tick={{ fontSize: 10 }} />
                          <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={110} />
                          <Tooltip formatter={(v) => [Number(v).toFixed(4), t('prediccion.transformer.peso')]} />
                          <Bar dataKey="peso" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {featureData.length > 0 && (
                      <div className="card">
                        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1">
                          <Info className="w-4 h-4 text-gray-400" /> {t('prediccion.transformer.importancia_titulo')}
                        </h2>
                        <ResponsiveContainer width="100%" height={180}>
                          <RadarChart data={featureData}>
                            <PolarGrid />
                            <PolarAngleAxis dataKey="feature" tick={{ fontSize: 9 }} />
                            <PolarRadiusAxis angle={30} tick={{ fontSize: 8 }} />
                            <Radar name={t('prediccion.transformer.importancia')} dataKey="importancia" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
                            <Tooltip formatter={(v) => [`${v}%`, t('prediccion.transformer.importancia')]} />
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
                      {t('comparacion.titulo')}
                    </h2>
                    <p className="text-xs text-indigo-600 mt-0.5">
                      {t('comparacion.subtitulo', {
                        entrenamiento: comparacion.n_datos_entrenamiento,
                        prueba: comparacion.n_datos_prueba,
                      })}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 bg-white border border-indigo-300 rounded-lg px-3 py-2 shadow-sm">
                    <Trophy className="w-5 h-5 text-yellow-500" />
                    <div>
                      <p className="text-xs text-gray-500">{t('comparacion.modelo_ganador_label')}</p>
                      <p className="text-sm font-bold text-indigo-700">
                        {comparacion.modelo_ganador_legible}
                      </p>
                      <p className="text-xs text-gray-400">{t('comparacion.mae_ganador', { valor: comparacion.mae_ganador })}</p>
                    </div>
                  </div>
                </div>
                {tiempoCompMs && (
                  <p className="text-xs text-indigo-400 mt-2">{t('tiempo_computo', { ms: tiempoCompMs })}</p>
                )}
              </div>

              {/* Tabla comparativa de métricas */}
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-indigo-500" />
                  {t('comparacion.metricas_titulo')}
                  <span className="text-xs font-normal text-gray-400 ml-1">
                    {t('comparacion.metricas_nota')}
                  </span>
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left px-3 py-2 text-xs font-semibold text-gray-600">{t('comparacion.columnas.modelo')}</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">{t('comparacion.columnas.mae')}</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">{t('comparacion.columnas.rmse')}</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">{t('comparacion.columnas.mape')}</th>
                        <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">{t('comparacion.columnas.r2')}</th>
                        <th className="text-center px-3 py-2 text-xs font-semibold text-gray-600">{t('comparacion.columnas.estado')}</th>
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
                                  {t('comparacion.badge_error')}
                                </span>
                              ) : esGanador ? (
                                <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium flex items-center gap-0.5 justify-center">
                                  <CheckCircle2 className="w-3 h-3" /> {t('comparacion.badge_ganador')}
                                </span>
                              ) : (
                                <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                                  {t('comparacion.badge_evaluado')}
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
                    {t('pruebas_estadisticas.dm_titulo')}
                    <span className="text-xs font-normal text-gray-400 ml-2">
                      {t('pruebas_estadisticas.dm_hipotesis')}
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
                              {dm.modelo_1} {t('pruebas_estadisticas.vs')} {dm.modelo_2}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">{dm.interpretacion}</p>
                          </div>
                          <div className="flex gap-3 text-xs text-right">
                            <div>
                              <p className="text-gray-400">{t('pruebas_estadisticas.estadistico_label')}</p>
                              <p className="font-mono font-semibold text-gray-700">
                                {dm.estadistico !== null ? dm.estadistico : '—'}
                              </p>
                            </div>
                            <div>
                              <p className="text-gray-400">{t('pruebas_estadisticas.p_valor_label')}</p>
                              <p className={`font-mono font-semibold ${
                                dm.significativo ? 'text-green-700' : 'text-gray-700'
                              }`}>
                                {dm.p_valor !== null ? dm.p_valor : '—'}
                              </p>
                            </div>
                            <div>
                              <p className="text-gray-400">{t('pruebas_estadisticas.significativo_label')}</p>
                              <p className={`font-semibold ${dm.significativo ? 'text-green-600' : 'text-gray-500'}`}>
                                {dm.significativo ? t('pruebas_estadisticas.significativo_si') : t('pruebas_estadisticas.significativo_no')}
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
                    {t('predicciones_futuras.titulo', { modelo: comparacion.modelo_ganador_legible })}
                  </h2>
                  <p className="text-xs text-gray-400 mb-4">
                    {t('predicciones_futuras.subtitulo')}
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
                        stroke="#6366f1" strokeWidth={2.5} name={t('prediccion.serie_demanda')} dot={{ r: 4 }}
                      />
                      <Line
                        type="monotone" dataKey="recomendacion"
                        stroke="#f59e0b" strokeWidth={2} strokeDasharray="6 3"
                        name={t('prediccion.serie_produccion')} dot={{ r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>

                  {/* Tabla de predicciones futuras */}
                  <div className="overflow-x-auto mt-4">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-gray-50">
                          <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">{t('predicciones_futuras.columnas.fecha')}</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">{t('predicciones_futuras.columnas.demanda_est')}</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">{t('predicciones_futuras.columnas.produccion_rec')}</th>
                          <th className="px-3 py-2 text-xs font-semibold text-gray-500">{t('predicciones_futuras.columnas.riesgo')}</th>
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
                      {t('comparacion.interpretacion_titulo')}
                    </h4>
                    <p className="text-xs text-blue-700 leading-relaxed">
                      {comparacion.explicacion}
                    </p>
                    <p className="text-xs text-blue-600 mt-2 font-medium">
                      {t('comparacion.interpretacion_nota')}
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
