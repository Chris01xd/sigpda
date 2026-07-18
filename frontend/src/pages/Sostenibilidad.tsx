import { useEffect, useState } from 'react'
import { Leaf, Droplets, TrendingDown, TrendingUp, Flame, Car, ShowerHead, RefreshCw } from 'lucide-react'
import api from '../api/client'

interface Huella {
  periodo_dias: number
  total_co2_kg: number
  total_agua_litros: number
  total_kg_desperdiciado: number
  total_costo_soles: number
  equivalencias: { arboles_anuales: number; km_en_auto: number; duchas_perdidas: number }
  por_categoria: { categoria: string; co2_kg: number; agua_litros: number; kg_desperdiciado: number; costo: number }[]
}

interface Ahorro {
  periodo_dias: number
  costo_actual: number
  costo_anterior: number
  ahorro_periodo: number
  porcentaje_mejora: number
  total_historico: number
  tendencia: string
}

const PERIODOS = [
  { label: '7 días',  value: 7 },
  { label: '30 días', value: 30 },
  { label: '90 días', value: 90 },
]

export default function Sostenibilidad() {
  const [dias,    setDias]    = useState(30)
  const [huella,  setHuella]  = useState<Huella | null>(null)
  const [ahorro,  setAhorro]  = useState<Ahorro | null>(null)
  const [loading, setLoading] = useState(false)

  const cargar = (d: number) => {
    setLoading(true)
    Promise.all([
      api.get(`/sostenibilidad/huella-carbono?dias=${d}`),
      api.get(`/sostenibilidad/ahorro-economico?dias=${d}`),
    ]).then(([h, a]) => {
      setHuella(h.data)
      setAhorro(a.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { cargar(dias) }, [])

  const tendColor = ahorro?.tendencia === 'mejora'
    ? 'text-green-600' : ahorro?.tendencia === 'empeora'
    ? 'text-red-600' : 'text-gray-500'

  const tendIcon = ahorro?.tendencia === 'mejora'
    ? <TrendingDown className="w-5 h-5 text-green-600" />
    : <TrendingUp className="w-5 h-5 text-red-500" />

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Leaf className="w-6 h-6 text-green-600" />
            Sostenibilidad e Impacto Ambiental
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Huella de carbono e hídrica generada por el desperdicio alimentario
          </p>
        </div>
        <div className="flex gap-2 items-center">
          {PERIODOS.map(p => (
            <button
              key={p.value}
              onClick={() => { setDias(p.value); cargar(p.value) }}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                dias === p.value
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {p.label}
            </button>
          ))}
          <button onClick={() => cargar(dias)} disabled={loading}
            className="ml-2 p-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {loading && <div className="text-center py-16 text-gray-400">Calculando...</div>}

      {!loading && huella && ahorro && (
        <>
          {/* KPIs Huella */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="card p-4 border-l-4 border-red-500">
              <div className="flex items-center gap-2 mb-1">
                <Flame className="w-4 h-4 text-red-500" />
                <p className="text-xs text-gray-500">CO₂ Equivalente</p>
              </div>
              <p className="text-2xl font-bold text-red-600">{huella.total_co2_kg} <span className="text-sm font-normal">kg</span></p>
              <p className="text-xs text-gray-400 mt-1">últimos {dias} días</p>
            </div>
            <div className="card p-4 border-l-4 border-blue-500">
              <div className="flex items-center gap-2 mb-1">
                <Droplets className="w-4 h-4 text-blue-500" />
                <p className="text-xs text-gray-500">Agua desperdiciada</p>
              </div>
              <p className="text-2xl font-bold text-blue-600">{huella.total_agua_litros.toLocaleString()} <span className="text-sm font-normal">L</span></p>
              <p className="text-xs text-gray-400 mt-1">últimos {dias} días</p>
            </div>
            <div className="card p-4 border-l-4 border-orange-500">
              <div className="flex items-center gap-2 mb-1">
                <Leaf className="w-4 h-4 text-orange-500" />
                <p className="text-xs text-gray-500">Alimentos desperdiciados</p>
              </div>
              <p className="text-2xl font-bold text-orange-600">{huella.total_kg_desperdiciado} <span className="text-sm font-normal">kg</span></p>
              <p className="text-xs text-gray-400 mt-1">últimos {dias} días</p>
            </div>
            <div className="card p-4 border-l-4 border-purple-500">
              <div className="flex items-center gap-2 mb-1">
                <TrendingDown className="w-4 h-4 text-purple-500" />
                <p className="text-xs text-gray-500">Costo desperdiciado</p>
              </div>
              <p className="text-2xl font-bold text-purple-600">S/ {huella.total_costo_soles.toFixed(2)}</p>
              <p className="text-xs text-gray-400 mt-1">últimos {dias} días</p>
            </div>
          </div>

          {/* Equivalencias */}
          <div className="card p-5 mb-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Equivalencias del impacto ambiental</h2>
            <div className="grid grid-cols-3 gap-6 text-center">
              <div>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <Leaf className="w-6 h-6 text-green-600" />
                </div>
                <p className="text-3xl font-bold text-green-700">{huella.equivalencias.arboles_anuales}</p>
                <p className="text-xs text-gray-500 mt-1">árboles necesarios un año<br/>para absorber este CO₂</p>
              </div>
              <div>
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <Car className="w-6 h-6 text-gray-600" />
                </div>
                <p className="text-3xl font-bold text-gray-700">{huella.equivalencias.km_en_auto.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">km en auto equivalentes<br/>(0.21 kg CO₂/km promedio)</p>
              </div>
              <div>
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <ShowerHead className="w-6 h-6 text-blue-600" />
                </div>
                <p className="text-3xl font-bold text-blue-700">{huella.equivalencias.duchas_perdidas.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">duchas de 8 min equivalentes<br/>(65 L por ducha)</p>
              </div>
            </div>
            <p className="text-xs text-gray-400 text-center mt-4">
              Factores de emisión: FAO / Our World in Data 2023
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Ahorro económico */}
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                {tendIcon} Ahorro Económico
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-500">Costo este período</span>
                  <span className="font-semibold text-red-600">S/ {ahorro.costo_actual.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-500">Costo período anterior</span>
                  <span className="font-semibold text-gray-700">S/ {ahorro.costo_anterior.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-500">Ahorro / pérdida</span>
                  <span className={`font-bold text-lg ${tendColor}`}>
                    {ahorro.ahorro_periodo >= 0 ? '+' : ''}S/ {ahorro.ahorro_periodo.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-500">% de mejora</span>
                  <span className={`font-semibold ${tendColor}`}>
                    {ahorro.porcentaje_mejora > 0 ? '↓' : ahorro.porcentaje_mejora < 0 ? '↑' : '='} {Math.abs(ahorro.porcentaje_mejora).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-gray-500">Total histórico desperdiciado</span>
                  <span className="font-semibold text-gray-700">S/ {ahorro.total_historico.toFixed(2)}</span>
                </div>
              </div>
              <div className={`mt-4 rounded-lg p-3 text-sm font-medium text-center ${
                ahorro.tendencia === 'mejora' ? 'bg-green-50 text-green-700' :
                ahorro.tendencia === 'empeora' ? 'bg-red-50 text-red-700' : 'bg-gray-50 text-gray-600'
              }`}>
                {ahorro.tendencia === 'mejora'
                  ? `El restaurante redujo su desperdicio en S/ ${ahorro.ahorro_periodo.toFixed(2)} respecto al período anterior`
                  : ahorro.tendencia === 'empeora'
                  ? `El desperdicio aumentó S/ ${Math.abs(ahorro.ahorro_periodo).toFixed(2)} respecto al período anterior`
                  : 'Sin cambio respecto al período anterior'}
              </div>
            </div>

            {/* Por categoría */}
            <div className="card p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Impacto por categoría de alimento</h2>
              {huella.por_categoria.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">Sin datos en el período</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="text-left px-2 py-2 text-gray-500">Categoría</th>
                        <th className="text-right px-2 py-2 text-gray-500">kg</th>
                        <th className="text-right px-2 py-2 text-gray-500">CO₂ kg</th>
                        <th className="text-right px-2 py-2 text-gray-500">Agua L</th>
                        <th className="text-right px-2 py-2 text-gray-500">Costo S/</th>
                      </tr>
                    </thead>
                    <tbody>
                      {huella.por_categoria.map((c, i) => (
                        <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="px-2 py-1.5 font-medium text-gray-700">{c.categoria}</td>
                          <td className="px-2 py-1.5 text-right text-gray-600">{c.kg_desperdiciado.toFixed(2)}</td>
                          <td className="px-2 py-1.5 text-right text-red-600 font-medium">{c.co2_kg.toFixed(2)}</td>
                          <td className="px-2 py-1.5 text-right text-blue-600">{c.agua_litros.toLocaleString()}</td>
                          <td className="px-2 py-1.5 text-right text-gray-700">{c.costo.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
