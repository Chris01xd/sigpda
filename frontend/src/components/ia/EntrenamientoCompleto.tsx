import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import { Trophy, Clock, Sliders, Layers, FlaskConical, AlertTriangle, Save, Download, Loader2 } from 'lucide-react'
import type { EntrenarCompararResultado, NombreModelo5 } from '../../types/ia'
import { NOMBRES_5_MODELOS, NOMBRES_5_MODELOS_LEGIBLES } from '../../types/ia'
import api from '../../api/client'

type FormatoReporte = 'pdf' | 'word' | 'excel'

const REPORTE_CONFIG: Record<FormatoReporte, { extension: string; mime: string; etiqueta: string }> = {
  pdf: { extension: 'pdf', mime: 'application/pdf', etiqueta: 'PDF' },
  word: { extension: 'docx', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', etiqueta: 'Word' },
  excel: { extension: 'xlsx', mime: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', etiqueta: 'Excel' },
}

const riesgoColor: Record<string, string> = {
  bajo: 'bg-green-100 text-green-700',
  medio: 'bg-yellow-100 text-yellow-700',
  alto: 'bg-red-100 text-red-700',
}

function fmt(v: number | null | undefined, dec = 4): string {
  return v === null || v === undefined || Number.isNaN(v) ? '—' : v.toFixed(dec)
}

function fmtHp(hp: Record<string, unknown> | null | undefined): string {
  if (!hp || Object.keys(hp).length === 0) return '—'
  return Object.entries(hp).map(([k, v]) => `${k}=${String(v)}`).join(', ')
}

interface Props {
  data: EntrenarCompararResultado
}

export default function EntrenamientoCompleto({ data }: Props) {
  const { t } = useTranslation('ia_paneles')
  const {
    dataset, modelo_ganador, modelo_ganador_legible, mae_ganador, criterio_seleccion,
    metricas_por_modelo, validacion_cruzada, hiperparametros, pruebas_estadisticas,
    modelo_guardado, predicciones_futuras, duracion_total_segundos, interpretacion,
    ejecucion_id,
  } = data

  const [descargando, setDescargando] = useState<FormatoReporte | null>(null)
  const [errorDescarga, setErrorDescarga] = useState('')

  const descargarReporte = async (formato: FormatoReporte) => {
    if (!ejecucion_id) return
    setDescargando(formato)
    setErrorDescarga('')
    try {
      const cfg = REPORTE_CONFIG[formato]
      const r = await api.get(`/reportes/ia/${ejecucion_id}/${formato}`, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([r.data], { type: cfg.mime }))
      const link = document.createElement('a')
      link.href = url
      link.download = `SIGPDA_IA_${ejecucion_id}.${cfg.extension}`
      link.click()
      URL.revokeObjectURL(url)
    } catch {
      setErrorDescarga(t('entrenamiento.error_descarga'))
    } finally {
      setDescargando(null)
    }
  }

  return (
    <div className="space-y-4">
      {/* Encabezado */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-base font-bold text-indigo-800 flex items-center gap-2">
              <FlaskConical className="w-5 h-5" /> {t('entrenamiento.titulo')}
            </h2>
            <p className="text-xs text-indigo-600 mt-0.5">
              {t('entrenamiento.resumen_dataset', {
                registros: dataset.registros, inicio: dataset.fecha_inicio, fin: dataset.fecha_fin,
                train: data.n_datos_entrenamiento, prueba: data.n_datos_prueba,
              })}
            </p>
            <p className="text-xs text-gray-400 flex items-center gap-1 mt-1">
              <Clock className="w-3 h-3" /> {t('entrenamiento.tiempo_total', { segundos: duracion_total_segundos })}
            </p>
          </div>
          <div className="flex items-center gap-2 bg-white border border-indigo-300 rounded-lg px-3 py-2 shadow-sm">
            <Trophy className="w-5 h-5 text-yellow-500" />
            <div>
              <p className="text-xs text-gray-500">{t('entrenamiento.modelo_ganador')}</p>
              <p className="text-sm font-bold text-indigo-700">{modelo_ganador_legible}</p>
              <p className="text-xs text-gray-400">{t('entrenamiento.mae_criterio', { mae: mae_ganador, criterio: criterio_seleccion })}</p>
            </div>
          </div>
        </div>

        {dataset.advertencias.length > 0 && (
          <div className="mt-3 space-y-1">
            {dataset.advertencias.map((a, i) => (
              <p key={i} className="text-xs text-amber-700 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 flex-shrink-0" /> {a}
              </p>
            ))}
          </div>
        )}

        <div className="mt-2 flex items-center gap-2 text-xs">
          <Save className="w-3.5 h-3.5 text-gray-400" />
          {modelo_guardado.guardado ? (
            <span className="text-green-700">
              {t('entrenamiento.modelo_guardado_ok', { tipo: modelo_guardado.tipo_modelo })}
            </span>
          ) : (
            <span className="text-gray-400">
              {modelo_guardado.motivo || t('entrenamiento.modelo_no_guardado')}
            </span>
          )}
        </div>

        {ejecucion_id && (
          <div className="mt-3 pt-3 border-t border-indigo-100">
            <p className="text-xs text-gray-500 mb-1.5">{t('entrenamiento.descargar_reporte', { id: ejecucion_id })}</p>
            <div className="flex gap-2 flex-wrap">
              {(Object.keys(REPORTE_CONFIG) as FormatoReporte[]).map((formato) => (
                <button
                  key={formato}
                  onClick={() => descargarReporte(formato)}
                  disabled={descargando !== null}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-gray-300
                             hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-medium text-gray-700"
                >
                  {descargando === formato ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                  {REPORTE_CONFIG[formato].etiqueta}
                </button>
              ))}
            </div>
            {errorDescarga && <p className="text-xs text-red-600 mt-1.5">{errorDescarga}</p>}
          </div>
        )}
      </div>

      {/* Tabla comparativa de 5 modelos */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          {t('entrenamiento.metricas_titulo')}
          <span className="text-xs font-normal text-gray-400 ml-1">{t('entrenamiento.metricas_nota')}</span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left px-3 py-2 text-xs font-semibold text-gray-600">{t('entrenamiento.columna_modelo')}</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">MAE</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">RMSE</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">MAPE (%)</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">SMAPE (%)</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600" title={t('entrenamiento.columna_u_theil_tooltip')}>{t('entrenamiento.columna_u_theil')}</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">R²</th>
                <th className="text-center px-3 py-2 text-xs font-semibold text-gray-600">{t('entrenamiento.columna_estado')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {NOMBRES_5_MODELOS.map((key) => {
                const m = metricas_por_modelo[key]
                const esGanador = key === modelo_ganador
                if (!m) return null
                return (
                  <tr key={key} className={esGanador ? 'bg-indigo-50 font-semibold' : 'hover:bg-gray-50'}>
                    <td className="px-3 py-2.5 flex items-center gap-2">
                      {esGanador && <Trophy className="w-4 h-4 text-yellow-500 flex-shrink-0" />}
                      <span className={esGanador ? 'text-indigo-700' : 'text-gray-700'}>
                        {NOMBRES_5_MODELOS_LEGIBLES[key]}
                      </span>
                    </td>
                    <td className={`px-3 py-2.5 text-right font-mono ${esGanador ? 'text-indigo-700' : ''}`}>{fmt(m.mae)}</td>
                    <td className="px-3 py-2.5 text-right font-mono">{fmt(m.rmse)}</td>
                    <td className="px-3 py-2.5 text-right font-mono">{fmt(m.mape, 2)}</td>
                    <td className="px-3 py-2.5 text-right font-mono">{fmt(m.smape, 2)}</td>
                    <td className="px-3 py-2.5 text-right font-mono">{fmt(m.u_theil)}</td>
                    <td className="px-3 py-2.5 text-right font-mono">{fmt(m.r2)}</td>
                    <td className="px-3 py-2.5 text-center">
                      {m.error ? (
                        <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">{t('entrenamiento.estado_error')}</span>
                      ) : esGanador ? (
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">{t('entrenamiento.estado_ganador')}</span>
                      ) : (
                        <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{t('entrenamiento.estado_evaluado')}</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Hiperparámetros (tuning) */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Sliders className="w-4 h-4 text-indigo-500" /> {t('entrenamiento.hiperparametros_titulo')}
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left px-3 py-2 text-xs font-semibold text-gray-600">{t('entrenamiento.columna_modelo')}</th>
                <th className="text-left px-3 py-2 text-xs font-semibold text-gray-600">{t('entrenamiento.columna_mejor_configuracion')}</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">{t('entrenamiento.columna_mejor_mae')}</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">{t('entrenamiento.columna_combinaciones')}</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">{t('entrenamiento.columna_tiempo')}</th>
                <th className="text-right px-3 py-2 text-xs font-semibold text-gray-600">{t('entrenamiento.columna_semilla')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {NOMBRES_5_MODELOS.map((key) => {
                const hp = hiperparametros[key]
                if (!hp) return null
                return (
                  <tr key={key} className="hover:bg-gray-50">
                    <td className="px-3 py-2.5 text-gray-700">{NOMBRES_5_MODELOS_LEGIBLES[key]}</td>
                    {hp.aplicable ? (
                      <>
                        <td className="px-3 py-2.5 text-xs font-mono text-gray-600">{fmtHp(hp.mejor_hiperparametros)}</td>
                        <td className="px-3 py-2.5 text-right font-mono">{fmt(hp.mejor_valor)}</td>
                        <td className="px-3 py-2.5 text-right">{hp.n_combinaciones ?? '—'}</td>
                        <td className="px-3 py-2.5 text-right">{hp.tiempo_total?.toFixed(2)}s</td>
                        <td className="px-3 py-2.5 text-right">{hp.semilla}</td>
                      </>
                    ) : (
                      <td colSpan={5} className="px-3 py-2.5 text-xs text-gray-400 italic">{hp.motivo || t('entrenamiento.no_aplicable')}</td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Validación cruzada */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-500" /> {t('entrenamiento.validacion_cruzada_titulo')}
        </h3>
        <div className="space-y-2">
          {NOMBRES_5_MODELOS.map((key) => {
            const cv = validacion_cruzada[key]
            if (!cv) return null
            return (
              <details key={key} className="border border-gray-200 rounded-lg overflow-hidden" open={key === modelo_ganador}>
                <summary className="cursor-pointer px-3 py-2 bg-gray-50 text-sm font-medium text-gray-700 flex items-center justify-between">
                  <span>{NOMBRES_5_MODELOS_LEGIBLES[key]}</span>
                  <span className="text-xs text-gray-400">
                    {t('entrenamiento.folds_resumen', {
                      ejecutados: cv.n_folds_ejecutados, solicitados: cv.n_folds_solicitados,
                      mae: fmt(cv.promedio.mae), desviacion: fmt(cv.desviacion_estandar.mae),
                    })}
                  </span>
                </summary>
                <div className="p-3">
                  {cv.advertencias.length > 0 && (
                    <p className="text-xs text-amber-600 mb-2">{cv.advertencias.join(' ')}</p>
                  )}
                  {cv.folds.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left px-2 py-1 font-semibold text-gray-500">{t('entrenamiento.columna_fold')}</th>
                            <th className="text-left px-2 py-1 font-semibold text-gray-500">{t('entrenamiento.columna_train')}</th>
                            <th className="text-left px-2 py-1 font-semibold text-gray-500">{t('entrenamiento.columna_validacion')}</th>
                            <th className="text-right px-2 py-1 font-semibold text-gray-500">MAE</th>
                            <th className="text-right px-2 py-1 font-semibold text-gray-500">RMSE</th>
                            <th className="text-right px-2 py-1 font-semibold text-gray-500">SMAPE</th>
                            <th className="text-right px-2 py-1 font-semibold text-gray-500" title={t('entrenamiento.columna_u_theil_tooltip')}>{t('entrenamiento.columna_u_theil')}</th>
                            <th className="text-right px-2 py-1 font-semibold text-gray-500">{t('entrenamiento.columna_tiempo')}</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {cv.folds.map((f) => (
                            <tr key={f.numero_fold}>
                              <td className="px-2 py-1">{f.numero_fold}</td>
                              <td className="px-2 py-1">{f.fecha_inicio_train} → {f.fecha_fin_train} ({f.n_train})</td>
                              <td className="px-2 py-1">{f.fecha_inicio_val} → {f.fecha_fin_val} ({f.n_val})</td>
                              <td className="px-2 py-1 text-right font-mono">{f.error ? '—' : fmt(f.mae, 3)}</td>
                              <td className="px-2 py-1 text-right font-mono">{f.error ? '—' : fmt(f.rmse, 3)}</td>
                              <td className="px-2 py-1 text-right font-mono">{f.error ? '—' : fmt(f.smape, 2)}</td>
                              <td className="px-2 py-1 text-right font-mono">{f.error ? 'N/D' : fmt(f.u_theil, 3)}</td>
                              <td className="px-2 py-1 text-right font-mono">{f.tiempo_entrenamiento?.toFixed(3) ?? '—'}s</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400">{t('entrenamiento.sin_folds')}</p>
                  )}
                </div>
              </details>
            )
          })}
        </div>
      </div>

      {/* Pruebas estadísticas */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('entrenamiento.pruebas_titulo')}</h3>

        {/* Friedman */}
        <div className={`rounded-lg border p-3 mb-3 ${pruebas_estadisticas.friedman.significativo ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
          <p className="text-xs font-semibold text-gray-700">
            {t('entrenamiento.friedman_titulo')}
          </p>
          <p className="text-xs text-gray-500 mt-1">{pruebas_estadisticas.friedman.interpretacion}</p>
          {pruebas_estadisticas.friedman.aplicable && (
            <div className="flex gap-4 mt-2 text-xs">
              <span>{t('entrenamiento.estadistico')} <strong className="font-mono">{fmt(pruebas_estadisticas.friedman.estadistico)}</strong></span>
              <span>{t('entrenamiento.p_valor')} <strong className="font-mono">{fmt(pruebas_estadisticas.friedman.p_valor)}</strong></span>
            </div>
          )}
        </div>

        {/* Wilcoxon */}
        {pruebas_estadisticas.wilcoxon.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-gray-700 mb-2">
              {t('entrenamiento.wilcoxon_titulo', { ganador: modelo_ganador_legible })}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b">
                    <th className="text-left px-2 py-1 font-semibold text-gray-500">{t('entrenamiento.columna_competidor')}</th>
                    <th className="text-right px-2 py-1 font-semibold text-gray-500">{t('entrenamiento.columna_p_valor')}</th>
                    <th className="text-right px-2 py-1 font-semibold text-gray-500">{t('entrenamiento.columna_p_valor_ajustado')}</th>
                    <th className="text-center px-2 py-1 font-semibold text-gray-500">{t('entrenamiento.columna_significativo')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {pruebas_estadisticas.wilcoxon.map((w) => (
                    <tr key={w.modelo_b}>
                      <td className="px-2 py-1">{NOMBRES_5_MODELOS_LEGIBLES[w.modelo_b as NombreModelo5] || w.modelo_b}</td>
                      <td className="px-2 py-1 text-right font-mono">{fmt(w.p_valor)}</td>
                      <td className="px-2 py-1 text-right font-mono">{fmt(w.p_valor_ajustado)}</td>
                      <td className="px-2 py-1 text-center">
                        <span className={`px-2 py-0.5 rounded-full ${w.significativo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                          {w.significativo ? t('entrenamiento.si') : t('entrenamiento.no')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Diebold-Mariano */}
        {pruebas_estadisticas.diebold_mariano.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-700 mb-2">{t('entrenamiento.dm_titulo')}</p>
            <div className="space-y-2">
              {pruebas_estadisticas.diebold_mariano.map((dm, i) => (
                <div key={i} className={`rounded-lg border p-2 text-xs ${dm.significativo ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
                  <p className="font-medium text-gray-700">{dm.modelo_1} vs {dm.modelo_2}</p>
                  <p className="text-gray-500">{dm.interpretacion}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Predicciones futuras */}
      {predicciones_futuras.length > 0 && (
        <div className="card">
          <h3 className="text-base font-semibold text-gray-700 mb-1">{t('entrenamiento.predicciones_titulo', { modelo: modelo_ganador_legible })}</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={predicciones_futuras}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="fecha" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="demanda_estimada" stroke="#6366f1" strokeWidth={2.5} name={t('entrenamiento.demanda_estimada_serie')} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="recomendacion" stroke="#f59e0b" strokeWidth={2} strokeDasharray="6 3" name={t('entrenamiento.produccion_recomendada_serie')} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
          <div className="overflow-x-auto mt-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">{t('entrenamiento.columna_fecha')}</th>
                  <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">{t('entrenamiento.columna_demanda_est')}</th>
                  <th className="text-right px-3 py-2 text-xs font-semibold text-gray-500">{t('entrenamiento.columna_prod_recomendada')}</th>
                  <th className="px-3 py-2 text-xs font-semibold text-gray-500">{t('entrenamiento.columna_riesgo')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {predicciones_futuras.map((p) => (
                  <tr key={p.fecha} className="hover:bg-gray-50">
                    <td className="px-3 py-2.5 font-medium">{p.fecha}</td>
                    <td className="px-3 py-2.5 text-right font-semibold text-indigo-700">{p.demanda_estimada}</td>
                    <td className="px-3 py-2.5 text-right">{p.recomendacion}</td>
                    <td className="px-3 py-2.5">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riesgoColor[p.riesgo]}`}>{p.riesgo}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Interpretación */}
      {interpretacion.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div className="space-y-1">
            {interpretacion.map((texto, i) => (
              <p key={i} className="text-xs text-blue-700 leading-relaxed">{texto}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
