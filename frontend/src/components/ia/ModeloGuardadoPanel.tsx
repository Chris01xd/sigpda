import { useEffect, useState } from 'react'
import { Archive, Loader2, RefreshCcw, PlayCircle, CheckCircle2, AlertTriangle } from 'lucide-react'
import api from '../../api/client'
import type { ModeloVigenteResultado } from '../../types/ia'

const riesgoColor: Record<string, string> = {
  bajo: 'bg-green-100 text-green-700',
  medio: 'bg-yellow-100 text-yellow-700',
  alto: 'bg-red-100 text-red-700',
}

interface PrediccionGuardada {
  usando_modelo_guardado: boolean
  tipo_modelo_legible: string
  fecha_entrenamiento: string
  predicciones_futuras: { fecha: string; demanda_estimada: number; recomendacion: number; riesgo: string }[]
}

interface Props {
  idPlato: number
  diasAdelante: number
  clima: number
  evento: number
}

export default function ModeloGuardadoPanel({ idPlato, diasAdelante, clima, evento }: Props) {
  const [estado, setEstado] = useState<ModeloVigenteResultado | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [accionando, setAccionando] = useState<'predecir' | 'reentrenar' | null>(null)
  const [prediccion, setPrediccion] = useState<PrediccionGuardada | null>(null)

  const cargarEstado = () => {
    if (!idPlato) return
    setLoading(true)
    setError('')
    api.get(`/ia/modelos-guardados/${idPlato}`)
      .then((r) => setEstado(r.data))
      .catch((e: unknown) => {
        const err = e as { response?: { status?: number; data?: { detail?: string } } }
        if (err.response?.status === 404) {
          setEstado({ existe: false, vigente: false, metadata: null, recomienda_reentrenar: true, motivo: 'No hay modelo guardado para este plato.' })
        } else {
          setError(err.response?.data?.detail || 'Error al consultar el modelo guardado')
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    setPrediccion(null)
    cargarEstado()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idPlato])

  const predecir = async () => {
    setAccionando('predecir')
    setError('')
    try {
      const r = await api.post(`/ia/modelos-guardados/${idPlato}/predecir`, {
        dias_adelante: diasAdelante, clima, evento,
      })
      setPrediccion(r.data)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err.response?.data?.detail || 'Error al predecir con el modelo guardado')
    } finally {
      setAccionando(null)
    }
  }

  const reentrenar = async () => {
    setAccionando('reentrenar')
    setError('')
    setPrediccion(null)
    try {
      await api.post(`/ia/modelos-guardados/${idPlato}/reentrenar`, {
        dias_adelante: diasAdelante, clima, evento,
      })
      cargarEstado()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err.response?.data?.detail || 'Error al reentrenar el modelo')
    } finally {
      setAccionando(null)
    }
  }

  if (!idPlato) return null

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <Archive className="w-4 h-4 text-teal-600" /> Modelo guardado
        </h3>
        <button onClick={cargarEstado} disabled={loading} className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
          <RefreshCcw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} /> Actualizar
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-700 flex items-center gap-2 mb-2">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" /> {error}
        </div>
      )}

      {loading && !estado && (
        <div className="flex items-center gap-2 text-xs text-gray-400 py-4 justify-center">
          <Loader2 className="w-4 h-4 animate-spin" /> Consultando...
        </div>
      )}

      {estado && !estado.existe && (
        <p className="text-xs text-gray-400 py-2">No hay modelo guardado para este plato todavía.</p>
      )}

      {estado?.existe && estado.metadata && (
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            {estado.vigente ? (
              <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Vigente
              </span>
            ) : (
              <span className="bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Datos cambiaron
              </span>
            )}
            <span className="text-gray-500">{estado.motivo}</span>
          </div>
          <p><span className="text-gray-400">Modelo:</span> <strong>{estado.metadata.tipo_modelo_legible}</strong></p>
          <p><span className="text-gray-400">Entrenado:</span> {new Date(estado.metadata.fecha_entrenamiento).toLocaleString()}</p>
          <p><span className="text-gray-400">MAE:</span> {estado.metadata.metricas?.mae ?? '—'} · <span className="text-gray-400">R²:</span> {estado.metadata.metricas?.r2 ?? '—'}</p>
          <p><span className="text-gray-400">Rango de datos:</span> {estado.metadata.rango_temporal_datos.inicio} → {estado.metadata.rango_temporal_datos.fin} ({estado.metadata.n_registros} días)</p>
        </div>
      )}

      <div className="flex gap-2 mt-3">
        <button
          onClick={predecir}
          disabled={!estado?.existe || accionando !== null}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-medium transition-colors"
        >
          {accionando === 'predecir' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <PlayCircle className="w-3.5 h-3.5" />}
          Usar modelo guardado
        </button>
        <button
          onClick={reentrenar}
          disabled={accionando !== null}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-gray-700 text-xs font-medium transition-colors"
        >
          {accionando === 'reentrenar' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
          Reentrenar y guardar
        </button>
      </div>

      {prediccion && (
        <div className="mt-3 border-t border-gray-100 pt-3">
          <p className="text-xs font-medium text-gray-600 mb-2">
            Predicción con modelo guardado ({prediccion.tipo_modelo_legible}, sin reentrenar)
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b">
                  <th className="text-left px-2 py-1 font-semibold text-gray-500">Fecha</th>
                  <th className="text-right px-2 py-1 font-semibold text-gray-500">Demanda</th>
                  <th className="text-right px-2 py-1 font-semibold text-gray-500">Prod. rec.</th>
                  <th className="px-2 py-1 font-semibold text-gray-500">Riesgo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {prediccion.predicciones_futuras.map((p) => (
                  <tr key={p.fecha}>
                    <td className="px-2 py-1">{p.fecha}</td>
                    <td className="px-2 py-1 text-right font-mono">{p.demanda_estimada}</td>
                    <td className="px-2 py-1 text-right">{p.recomendacion}</td>
                    <td className="px-2 py-1">
                      <span className={`px-1.5 py-0.5 rounded-full ${riesgoColor[p.riesgo]}`}>{p.riesgo}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
