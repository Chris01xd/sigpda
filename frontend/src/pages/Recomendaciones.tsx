import { useEffect, useState } from 'react'
import { RefreshCw, AlertTriangle, Info, CheckCircle2, Clock } from 'lucide-react'
import api from '../api/client'
import { Recomendacion } from '../types'

const iconMap: Record<string, React.ReactNode> = {
  alta: <AlertTriangle className="w-5 h-5 text-red-500" />,
  media: <Clock className="w-5 h-5 text-yellow-500" />,
  baja: <Info className="w-5 h-5 text-blue-500" />,
}

const colorMap: Record<string, string> = {
  alta: 'border-red-200 bg-red-50',
  media: 'border-yellow-200 bg-yellow-50',
  baja: 'border-blue-200 bg-blue-50',
}

const badgeMap: Record<string, string> = {
  alta: 'bg-red-100 text-red-700',
  media: 'bg-yellow-100 text-yellow-700',
  baja: 'bg-blue-100 text-blue-700',
}

export default function Recomendaciones() {
  const [recomendaciones, setRecomendaciones] = useState<Recomendacion[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await api.get('/recomendaciones')
      setRecomendaciones(r.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const altas = recomendaciones.filter((r) => r.severidad === 'alta')
  const medias = recomendaciones.filter((r) => r.severidad === 'media')
  const bajas = recomendaciones.filter((r) => r.severidad === 'baja')

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Recomendaciones IA</h1>
          <p className="text-sm text-gray-500">Sugerencias inteligentes basadas en datos</p>
        </div>
        <button onClick={load} disabled={loading} className="btn-secondary flex items-center gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {recomendaciones.length === 0 && !loading && (
        <div className="card flex flex-col items-center py-12 text-center">
          <CheckCircle2 className="w-12 h-12 text-green-400 mb-3" />
          <p className="text-gray-600 font-medium">Sin alertas activas</p>
          <p className="text-sm text-gray-400 mt-1">El sistema no detecta problemas críticos en este momento</p>
        </div>
      )}

      {[
        { label: 'Alta prioridad', items: altas, key: 'alta' },
        { label: 'Prioridad media', items: medias, key: 'media' },
        { label: 'Informativas', items: bajas, key: 'baja' },
      ].map(({ label, items, key }) =>
        items.length > 0 ? (
          <div key={key} className="mb-6">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">{label} ({items.length})</h2>
            <div className="space-y-3">
              {items.map((r, i) => (
                <div key={i} className={`border rounded-xl p-4 flex gap-3 ${colorMap[r.severidad]}`}>
                  <div className="flex-shrink-0 mt-0.5">{iconMap[r.severidad]}</div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-semibold text-gray-800">{r.titulo}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${badgeMap[r.severidad]}`}>
                        {r.tipo.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{r.descripcion}</p>
                    <p className="text-xs text-gray-400 mt-2">Módulo: {r.modulo}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null
      )}
    </div>
  )
}
