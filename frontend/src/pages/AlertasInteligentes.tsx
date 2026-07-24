import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  BellRing, RefreshCw, CheckCheck, Eye,
  AlertTriangle, TrendingDown, Package, Clock,
  Layers, Lightbulb, ShieldAlert, Filter, X,
} from 'lucide-react'
import api from '../api/client'

// ——— Types ——————————————————————————————————————————

interface Alerta {
  id_alerta: number
  tipo_alerta: string
  nivel_riesgo: string
  titulo: string
  descripcion: string
  recomendacion: string
  fecha_generacion: string | null
  estado: string
  plato?: string | null
  insumo?: string | null
  valor_predicho?: number | null
  valor_actual?: number | null
  porcentaje_riesgo?: number | null
}

// ——— Helpers ————————————————————————————————————————

const NIVEL_BADGE: Record<string, string> = {
  CRITICO: 'bg-red-100 text-red-700 border border-red-300',
  ALTO:    'bg-orange-100 text-orange-700 border border-orange-300',
  MEDIO:   'bg-yellow-100 text-yellow-700 border border-yellow-200',
  BAJO:    'bg-blue-100 text-blue-700 border border-blue-200',
}

const NIVEL_CARD: Record<string, string> = {
  CRITICO: 'border-l-4 border-red-500 bg-red-50',
  ALTO:    'border-l-4 border-orange-500 bg-orange-50',
  MEDIO:   'border-l-4 border-yellow-400 bg-yellow-50',
  BAJO:    'border-l-4 border-blue-400 bg-blue-50',
}

const TIPO_ICON: Record<string, JSX.Element> = {
  RIESGO_SOBREPRODUCCION:  <AlertTriangle className="w-5 h-5 text-orange-500" />,
  PRODUCTO_PROXIMO_VENCER: <Clock         className="w-5 h-5 text-red-500" />,
  STOCK_EXCESIVO:          <Package       className="w-5 h-5 text-yellow-500" />,
  BAJA_DEMANDA:            <TrendingDown  className="w-5 h-5 text-blue-500" />,
  ALTO_DESPERDICIO:        <Layers        className="w-5 h-5 text-orange-600" />,
  RECOMENDACION_MENU:      <Lightbulb     className="w-5 h-5 text-indigo-500" />,
  ALERTA_CRITICA:          <ShieldAlert   className="w-5 h-5 text-red-600" />,
}

const TIPOS_FILTRO = [
  'RIESGO_SOBREPRODUCCION', 'PRODUCTO_PROXIMO_VENCER', 'STOCK_EXCESIVO',
  'BAJA_DEMANDA', 'ALTO_DESPERDICIO', 'RECOMENDACION_MENU', 'ALERTA_CRITICA',
]
const NIVELES_FILTRO = ['CRITICO', 'ALTO', 'MEDIO', 'BAJO']
const ESTADOS_FILTRO = ['pendiente', 'leida', 'resuelta']

function fmtDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

// ——— Component ——————————————————————————————————————

export default function AlertasInteligentes() {
  const { t } = useTranslation('alertas_inteligentes')
  const [alertas, setAlertas]         = useState<Alerta[]>([])
  const [loading, setLoading]         = useState(false)
  const [generating, setGenerating]   = useState(false)
  const [error, setError]             = useState<string | null>(null)
  const [success, setSuccess]         = useState<string | null>(null)

  // Filtros
  const [filTipo,   setFilTipo]   = useState('')
  const [filNivel,  setFilNivel]  = useState('')
  const [filEstado, setFilEstado] = useState('pendiente')

  // Parámetros de generación
  const [clima,  setClima]  = useState(2)
  const [evento, setEvento] = useState(0)

  // Detalle modal
  const [detalle, setDetalle] = useState<Alerta | null>(null)

  const cargar = () => {
    setLoading(true)
    setError(null)
    const params: Record<string, string | number> = { limit: 100, estado: filEstado }
    if (filTipo)  params.tipo  = filTipo
    if (filNivel) params.nivel = filNivel

    api.get('/alertas-inteligentes', { params })
      .then((r) => setAlertas(r.data))
      .catch(() => setError(t('mensajes.error_cargar')))
      .finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [filTipo, filNivel, filEstado])

  const generar = () => {
    setGenerating(true)
    setError(null)
    setSuccess(null)
    api.post('/alertas-inteligentes/generar', { clima, evento })
      .then((r) => {
        const { total_generadas } = r.data
        setSuccess(t('mensajes.generadas', { count: total_generadas }))
        cargar()
      })
      .catch(() => setError(t('mensajes.error_generar')))
      .finally(() => setGenerating(false))
  }

  const marcarLeida = (id: number) => {
    api.put(`/alertas-inteligentes/${id}/marcar-leida`).then(cargar)
  }

  const resolver = (id: number) => {
    api.put(`/alertas-inteligentes/${id}/resolver`).then(() => {
      if (detalle?.id_alerta === id) setDetalle(null)
      cargar()
    })
  }

  // Resumen por nivel (solo pendientes visibles)
  const conteo = alertas.reduce<Record<string, number>>((acc, a) => {
    acc[a.nivel_riesgo] = (acc[a.nivel_riesgo] || 0) + 1
    return acc
  }, {})

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <BellRing className="w-6 h-6 text-orange-500" />
            {t('titulo')}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {t('subtitulo')}
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-500">{t('config.clima')}</label>
            <select
              value={clima}
              onChange={(e) => setClima(Number(e.target.value))}
              className="input text-sm py-1.5 pr-7"
            >
              <option value={1}>☀️ {t('config.clima_opciones.soleado')}</option>
              <option value={2}>☁️ {t('config.clima_opciones.nublado')}</option>
              <option value={3}>🌧️ {t('config.clima_opciones.lluvioso')}</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-500">{t('config.evento')}</label>
            <select
              value={evento}
              onChange={(e) => setEvento(Number(e.target.value))}
              className="input text-sm py-1.5 pr-7"
            >
              <option value={0}>{t('config.evento_opciones.sin_evento')}</option>
              <option value={1}>{t('config.evento_opciones.evento_local')}</option>
              <option value={2}>{t('config.evento_opciones.feriado_nacional')}</option>
            </select>
          </div>
          <button
            onClick={generar}
            disabled={generating}
            className="btn-primary flex items-center gap-2 py-2"
          >
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? t('config.generando') : t('config.generar')}
          </button>
        </div>
      </div>

      {/* Mensajes de feedback */}
      {error   && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>}
      {success && <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">{success}</div>}

      {/* KPI chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        {(['CRITICO', 'ALTO', 'MEDIO', 'BAJO'] as const).map((n) => (
          <span key={n} className={`px-3 py-1 rounded-full text-xs font-semibold ${NIVEL_BADGE[n]}`}>
            {n}: {conteo[n] || 0}
          </span>
        ))}
        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600">
          {t('resumen.total')}: {alertas.length}
        </span>
      </div>

      {/* Filtros */}
      <div className="card mb-6 flex flex-wrap gap-4 items-end">
        <Filter className="w-4 h-4 text-gray-400 mt-auto mb-1" />
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">{t('filtros.estado')}</label>
          <div className="flex gap-1">
            {ESTADOS_FILTRO.map((e) => (
              <button
                key={e}
                onClick={() => setFilEstado(e)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  filEstado === e
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {t(`filtros.estados.${e}`)}
              </button>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">{t('filtros.tipo')}</label>
          <select
            value={filTipo}
            onChange={(e) => setFilTipo(e.target.value)}
            className="input text-sm py-1.5 pr-7"
          >
            <option value="">{t('filtros.todos')}</option>
            {TIPOS_FILTRO.map((tipo) => (
              <option key={tipo} value={tipo}>{t(`tipos.${tipo}`)}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">{t('filtros.nivel')}</label>
          <select
            value={filNivel}
            onChange={(e) => setFilNivel(e.target.value)}
            className="input text-sm py-1.5 pr-7"
          >
            <option value="">{t('filtros.todos')}</option>
            {NIVELES_FILTRO.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
        {(filTipo || filNivel) && (
          <button
            onClick={() => { setFilTipo(''); setFilNivel('') }}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mt-auto mb-1"
          >
            <X className="w-3 h-3" /> {t('filtros.limpiar')}
          </button>
        )}
      </div>

      {/* Lista de alertas */}
      {loading ? (
        <div className="text-center py-16 text-gray-400">{t('lista.cargando')}</div>
      ) : alertas.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <BellRing className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p>{t('lista.vacio', { estado: t(`filtros.estados.${filEstado}`).toLowerCase() })}</p>
          <p className="text-xs mt-1">{t('lista.ayuda_generar')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {alertas.map((a) => (
            <div
              key={a.id_alerta}
              className={`rounded-xl p-4 shadow-sm ${NIVEL_CARD[a.nivel_riesgo] ?? 'border-l-4 border-gray-300 bg-gray-50'}`}
            >
              {/* Card header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  {TIPO_ICON[a.tipo_alerta] ?? <BellRing className="w-5 h-5 text-gray-400" />}
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${NIVEL_BADGE[a.nivel_riesgo]}`}>
                    {a.nivel_riesgo}
                  </span>
                </div>
                <span className="text-xs text-gray-400 shrink-0">
                  {t(`tipos.${a.tipo_alerta}`, { defaultValue: a.tipo_alerta })}
                </span>
              </div>

              {/* Título */}
              <p className="font-semibold text-gray-800 text-sm leading-tight mb-1">{a.titulo}</p>

              {/* Descripción */}
              <p className="text-xs text-gray-600 line-clamp-2 mb-3">{a.descripcion}</p>

              {/* Meta: recurso y fecha */}
              <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-400 mb-3">
                {(a.plato || a.insumo) && (
                  <span>📌 {a.plato ?? a.insumo}</span>
                )}
                {a.porcentaje_riesgo != null && (
                  <span>⚠️ {t('tarjeta.riesgo', { valor: a.porcentaje_riesgo.toFixed(1) })}</span>
                )}
                <span>{fmtDate(a.fecha_generacion)}</span>
              </div>

              {/* Acciones */}
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={() => setDetalle(a)}
                  className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  <Eye className="w-3.5 h-3.5" /> {t('tarjeta.ver_detalle')}
                </button>
                {a.estado === 'pendiente' && (
                  <button
                    onClick={() => marcarLeida(a.id_alerta)}
                    className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" /> {t('tarjeta.marcar_leida')}
                  </button>
                )}
                {a.estado !== 'resuelta' && (
                  <button
                    onClick={() => resolver(a.id_alerta)}
                    className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors"
                  >
                    <CheckCheck className="w-3.5 h-3.5" /> {t('tarjeta.resolver')}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal de detalle */}
      {detalle && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
          onClick={() => setDetalle(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className={`p-5 rounded-t-2xl ${NIVEL_CARD[detalle.nivel_riesgo] ?? 'bg-gray-50'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {TIPO_ICON[detalle.tipo_alerta]}
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${NIVEL_BADGE[detalle.nivel_riesgo]}`}>
                    {detalle.nivel_riesgo}
                  </span>
                </div>
                <button onClick={() => setDetalle(null)} className="text-gray-400 hover:text-gray-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <h2 className="font-bold text-gray-800 text-base mt-3 leading-tight">{detalle.titulo}</h2>
              <p className="text-xs text-gray-500 mt-1">{t(`tipos.${detalle.tipo_alerta}`, { defaultValue: detalle.tipo_alerta })}</p>
            </div>

            <div className="p-5 space-y-4">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">{t('modal.descripcion')}</p>
                <p className="text-sm text-gray-700">{detalle.descripcion}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">{t('modal.recomendacion')}</p>
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
                  <p className="text-sm text-indigo-800">{detalle.recomendacion}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {detalle.plato && (
                  <div><p className="text-xs text-gray-400">{t('modal.plato')}</p><p className="font-medium">{detalle.plato}</p></div>
                )}
                {detalle.insumo && (
                  <div><p className="text-xs text-gray-400">{t('modal.insumo')}</p><p className="font-medium">{detalle.insumo}</p></div>
                )}
                {detalle.porcentaje_riesgo != null && (
                  <div><p className="text-xs text-gray-400">{t('modal.porcentaje_riesgo')}</p><p className="font-medium">{detalle.porcentaje_riesgo.toFixed(1)} %</p></div>
                )}
                {detalle.valor_actual != null && (
                  <div><p className="text-xs text-gray-400">{t('modal.valor_actual')}</p><p className="font-medium">{detalle.valor_actual.toFixed(2)}</p></div>
                )}
                <div>
                  <p className="text-xs text-gray-400">{t('modal.generada')}</p>
                  <p className="font-medium">{fmtDate(detalle.fecha_generacion)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">{t('modal.estado')}</p>
                  <p className="font-medium capitalize">{detalle.estado}</p>
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                {detalle.estado === 'pendiente' && (
                  <button
                    onClick={() => { marcarLeida(detalle.id_alerta); setDetalle(null) }}
                    className="flex-1 btn-secondary py-2 text-sm flex items-center justify-center gap-2"
                  >
                    <Eye className="w-4 h-4" /> {t('modal.marcar_leida')}
                  </button>
                )}
                {detalle.estado !== 'resuelta' && (
                  <button
                    onClick={() => resolver(detalle.id_alerta)}
                    className="flex-1 btn-primary py-2 text-sm flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700"
                  >
                    <CheckCheck className="w-4 h-4" /> {t('modal.resolver_alerta')}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
