import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { AlertTriangle, ClipboardList, CalendarDays, Copy, Sigma } from 'lucide-react'
import type { EdaResultado } from '../../types/ia'

function etiquetaCorrelacion(t: TFunction, campo: string): string {
  const mapa: Record<string, string> = {
    cantidad: t('eda.correlacion_campos.cantidad'),
    precio: t('eda.correlacion_campos.precio'),
    dia_semana: t('eda.correlacion_campos.dia_semana'),
    mes: t('eda.correlacion_campos.mes'),
    es_finde: t('eda.correlacion_campos.es_finde'),
    clima: t('eda.correlacion_campos.clima'),
    evento: t('eda.correlacion_campos.evento'),
    ventas_7d: t('eda.correlacion_campos.ventas_7d'),
  }
  return mapa[campo] || campo
}

function colorCorrelacion(v: number | null): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '#e5e7eb'
  const alpha = Math.min(1, Math.abs(v)).toFixed(2)
  return v >= 0 ? `rgba(99, 102, 241, ${alpha})` : `rgba(239, 68, 68, ${alpha})`
}

function fmt(v: number | null | undefined, dec = 2): string {
  return v === null || v === undefined || Number.isNaN(v) ? '—' : v.toFixed(dec)
}

interface Props {
  data: EdaResultado
}

export default function EdaPanel({ data }: Props) {
  const { t } = useTranslation('ia_paneles')
  const {
    resumen, estadisticas_descriptivas: stats, valores_faltantes,
    duplicados, outliers, serie_historica, distribucion,
    por_dia_semana, por_mes, correlaciones, clima_evento, advertencias,
  } = data

  const sinDatos = resumen.registros_transacciones === 0
  const columnasCorr = Object.keys(correlaciones)
  const totalFaltantes = Object.values(valores_faltantes).reduce((a, b) => a + b, 0)

  // Datos para el histograma (distribución)
  const distribucionData = distribucion.map((b) => ({
    rango: `${b.rango_inicio.toFixed(0)}-${b.rango_fin.toFixed(0)}`,
    frecuencia: b.frecuencia,
  }))

  // Boxplot simplificado (sin librería adicional): posiciones en % dentro de [min, max]
  const boxplot = (() => {
    const { minimo, maximo, q1, q3, mediana } = stats
    if ([minimo, maximo, q1, q3, mediana].some((v) => v === undefined || v === null)) return null
    const rango = (maximo as number) - (minimo as number) || 1
    const pos = (v: number) => Math.max(0, Math.min(100, ((v - (minimo as number)) / rango) * 100))
    const fechaPorCantidad = new Map(serie_historica.map((p) => [p.fecha, p.cantidad]))
    const outlierPuntos = outliers.fechas
      .map((f) => fechaPorCantidad.get(f))
      .filter((v): v is number => v !== undefined)
    return {
      minPct: pos(minimo as number), q1Pct: pos(q1 as number),
      medPct: pos(mediana as number), q3Pct: pos(q3 as number), maxPct: pos(maximo as number),
      outlierPct: outlierPuntos.map(pos),
    }
  })()

  if (sinDatos) {
    return (
      <div className="card flex flex-col items-center justify-center py-12 text-center">
        <ClipboardList className="w-12 h-12 text-gray-200 mb-3" />
        <p className="text-gray-500 font-medium">{t('eda.sin_datos')}</p>
        {advertencias.map((a, i) => (
          <p key={i} className="text-xs text-gray-400 mt-1">{a}</p>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Advertencias */}
      {advertencias.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              {advertencias.map((a, i) => (
                <p key={i} className="text-xs text-amber-800">{a}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tarjetas resumen */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card py-3">
          <p className="text-xs text-gray-500">{t('eda.registros')}</p>
          <p className="text-xl font-bold text-gray-800">{resumen.registros_transacciones}</p>
          <p className="text-xs text-gray-400">{t('eda.dias_con_venta', { n: resumen.dias_con_venta })}</p>
        </div>
        <div className="card py-3">
          <p className="text-xs text-gray-500 flex items-center gap-1"><CalendarDays className="w-3 h-3" /> {t('eda.periodo')}</p>
          <p className="text-sm font-bold text-gray-800">{resumen.fecha_inicio} → {resumen.fecha_fin}</p>
          <p className="text-xs text-gray-400">{t('eda.dias_cubiertos', { n: resumen.dias_cubiertos })}</p>
        </div>
        <div className="card py-3">
          <p className="text-xs text-gray-500 flex items-center gap-1"><Copy className="w-3 h-3" /> {t('eda.duplicados')}</p>
          <p className="text-xl font-bold text-gray-800">{duplicados}</p>
          <p className="text-xs text-gray-400">{t('eda.valores_faltantes', { n: totalFaltantes })}</p>
        </div>
        <div className="card py-3">
          <p className="text-xs text-gray-500 flex items-center gap-1"><Sigma className="w-3 h-3" /> {t('eda.outliers_iqr')}</p>
          <p className="text-xl font-bold text-gray-800">{outliers.cantidad}</p>
          <p className="text-xs text-gray-400">
            {t('eda.limites', { inferior: fmt(outliers.limite_inferior), superior: fmt(outliers.limite_superior) })}
          </p>
        </div>
      </div>

      {/* Estadísticas descriptivas */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('eda.estadisticas_descriptivas_titulo')}</h3>
        <div className="grid grid-cols-4 md:grid-cols-8 gap-2 text-center">
          {([
            [t('eda.media'), stats.media], [t('eda.mediana'), stats.mediana], [t('eda.desviacion_estandar'), stats.desviacion_estandar],
            [t('eda.minimo'), stats.minimo], [t('eda.maximo'), stats.maximo], ['Q1', stats.q1],
            ['Q3', stats.q3], ['IQR', stats.rango_intercuartilico],
          ] as [string, number | undefined][]).map(([label, val]) => (
            <div key={label} className="bg-gray-50 rounded-lg p-2">
              <p className="text-xs text-gray-500">{label}</p>
              <p className="text-sm font-bold text-gray-800">{fmt(val)}</p>
            </div>
          ))}
        </div>

        {/* Boxplot simplificado */}
        {boxplot && (
          <div className="mt-5">
            <p className="text-xs text-gray-500 mb-2">{t('eda.boxplot_titulo')}</p>
            <div className="relative h-8">
              <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 h-0.5 bg-gray-300" />
              <div
                className="absolute top-1/2 -translate-y-1/2 h-4 bg-indigo-200 border border-indigo-400 rounded"
                style={{ left: `${boxplot.q1Pct}%`, width: `${Math.max(1, boxplot.q3Pct - boxplot.q1Pct)}%` }}
              />
              <div
                className="absolute top-1/2 -translate-y-1/2 h-5 w-0.5 bg-indigo-700"
                style={{ left: `${boxplot.medPct}%` }}
              />
              {boxplot.outlierPct.map((p, i) => (
                <div
                  key={i}
                  className="absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-red-500"
                  style={{ left: `${p}%` }}
                  title={t('eda.outlier_tooltip')}
                />
              ))}
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>{fmt(stats.minimo)}</span>
              <span>{fmt(stats.maximo)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Serie histórica */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          {t('eda.evolucion_titulo')}
          <span className="text-xs font-normal text-gray-400 ml-2">
            {t('eda.evolucion_nota')}
          </span>
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={serie_historica}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="fecha" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Line
              type="monotone" dataKey="cantidad" stroke="#6366f1" strokeWidth={1.5}
              dot={(props) => {
                const { cx, cy, payload, index } = props
                return (
                  <circle
                    key={`dot-${index}`}
                    cx={cx} cy={cy} r={payload.interpolado ? 3 : 1.5}
                    fill={payload.interpolado ? '#f59e0b' : '#6366f1'}
                  />
                )
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Histograma de distribución */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('eda.distribucion_titulo')}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={distribucionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="rango" tick={{ fontSize: 9 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="frecuencia" fill="#6366f1" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Demanda por día de semana */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('eda.dia_semana_titulo')}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={por_dia_semana}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="dia_semana" tick={{ fontSize: 9 }} interval={0} angle={-20} textAnchor="end" height={40} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [v.toFixed(2), t('eda.demanda_promedio')]} />
              <Bar dataKey="demanda_promedio" fill="#8b5cf6" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Demanda por mes */}
      {por_mes.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('eda.mes_titulo')}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={por_mes}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="mes" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [v.toFixed(2), t('eda.demanda_promedio')]} />
              <Bar dataKey="demanda_promedio" fill="#0ea5e9" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Mapa de calor de correlaciones */}
      {columnasCorr.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('eda.correlacion_titulo')}</h3>
          <div className="overflow-x-auto">
            <table className="text-xs border-collapse">
              <thead>
                <tr>
                  <th className="p-1" />
                  {columnasCorr.map((c) => (
                    <th key={c} className="p-1 font-medium text-gray-500" style={{ writingMode: 'vertical-rl' }}>
                      {etiquetaCorrelacion(t, c)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {columnasCorr.map((fila) => (
                  <tr key={fila}>
                    <td className="p-1 pr-2 font-medium text-gray-500 whitespace-nowrap">
                      {etiquetaCorrelacion(t, fila)}
                    </td>
                    {columnasCorr.map((col) => {
                      const v = correlaciones[fila]?.[col] ?? null
                      return (
                        <td
                          key={col}
                          className="w-10 h-8 text-center align-middle"
                          style={{ backgroundColor: colorCorrelacion(v) }}
                          title={t('eda.correlacion_detalle', { fila, col, valor: v === null ? t('eda.sin_variacion') : v })}
                        >
                          {v === null ? '' : v.toFixed(2)}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Clima / evento */}
      {clima_evento?.nota && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-3">
          <p className="text-xs text-blue-700">{clima_evento.nota}</p>
        </div>
      )}
    </div>
  )
}
