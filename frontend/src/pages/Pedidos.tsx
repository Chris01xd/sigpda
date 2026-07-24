import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ShoppingBag, RefreshCw, Package, TrendingUp } from 'lucide-react'
import api from '../api/client'

interface Pedido {
  id_insumo: number
  insumo: string
  proveedor: string
  unidad: string
  stock_actual: number
  necesario: number
  cantidad_pedido: number
  costo_estimado: number
}

interface Resumen {
  dias_proyeccion: number
  total_items: number
  total_costo_estimado: number
  pedidos: Pedido[]
}

const DIAS_OPTS = [5, 7, 14]

export default function Pedidos() {
  const { t } = useTranslation('pedidos')
  const [dias,    setDias]    = useState(7)
  const [data,    setData]    = useState<Resumen | null>(null)
  const [loading, setLoading] = useState(false)

  const cargar = (d: number) => {
    setLoading(true)
    api.get(`/dashboard/pedidos-sugeridos?dias=${d}`)
      .then(r => setData(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { cargar(dias) }, [])

  // Agrupar por proveedor
  const porProveedor = data
    ? data.pedidos.reduce<Record<string, Pedido[]>>((acc, p) => {
        ;(acc[p.proveedor] ??= []).push(p)
        return acc
      }, {})
    : {}

  return (
    <div>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <ShoppingBag className="w-6 h-6 text-indigo-600" />
            {t('titulo')}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {t('subtitulo')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{t('proyeccion')}</span>
          {DIAS_OPTS.map(d => (
            <button key={d} onClick={() => { setDias(d); cargar(d) }}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                dias === d ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}>
              {d} {t('dias_sufijo')}
            </button>
          ))}
          <button onClick={() => cargar(dias)} disabled={loading}
            className="ml-1 p-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {loading && <div className="text-center py-16 text-gray-400">{t('calculando')}</div>}

      {!loading && data && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="card p-4 border-l-4 border-indigo-500">
              <div className="flex items-center gap-2 mb-1">
                <Package className="w-4 h-4 text-indigo-500" />
                <p className="text-xs text-gray-500">{t('kpi.insumos_a_pedir')}</p>
              </div>
              <p className="text-3xl font-bold text-indigo-600">{data.total_items}</p>
              <p className="text-xs text-gray-400 mt-1">{t('kpi.proximos_dias', { dias })}</p>
            </div>
            <div className="card p-4 border-l-4 border-orange-500">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-4 h-4 text-orange-500" />
                <p className="text-xs text-gray-500">{t('kpi.costo_estimado')}</p>
              </div>
              <p className="text-2xl font-bold text-orange-600">S/ {data.total_costo_estimado.toFixed(2)}</p>
              <p className="text-xs text-gray-400 mt-1">{t('kpi.total_pedido')}</p>
            </div>
            <div className="card p-4 border-l-4 border-green-500">
              <div className="flex items-center gap-2 mb-1">
                <ShoppingBag className="w-4 h-4 text-green-500" />
                <p className="text-xs text-gray-500">{t('kpi.proveedores')}</p>
              </div>
              <p className="text-3xl font-bold text-green-600">{Object.keys(porProveedor).length}</p>
              <p className="text-xs text-gray-400 mt-1">{t('kpi.distintos_a_contactar')}</p>
            </div>
          </div>

          {data.total_items === 0 ? (
            <div className="card p-10 text-center text-gray-400">
              <Package className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium">{t('vacio.titulo', { dias })}</p>
              <p className="text-xs mt-1">{t('vacio.descripcion')}</p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(porProveedor).map(([proveedor, items]) => (
                <div key={proveedor} className="card">
                  <div className="flex items-center justify-between mb-3 pb-3 border-b border-gray-100">
                    <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                      <ShoppingBag className="w-4 h-4 text-indigo-500" />
                      {proveedor}
                    </h3>
                    <span className="text-sm text-gray-500">
                      {t('grupo.items_costo', { cantidad: items.length, costo: items.reduce((s, i) => s + i.costo_estimado, 0).toFixed(2) })}
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 text-xs text-gray-500">
                          <th className="text-left px-3 py-2">{t('tabla.insumo')}</th>
                          <th className="text-right px-3 py-2">{t('tabla.stock_actual')}</th>
                          <th className="text-right px-3 py-2">{t('tabla.necesario')}</th>
                          <th className="text-right px-3 py-2 text-indigo-600 font-semibold">{t('tabla.a_pedir')}</th>
                          <th className="text-right px-3 py-2">{t('tabla.unidad')}</th>
                          <th className="text-right px-3 py-2">{t('tabla.costo_est')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((p, i) => (
                          <tr key={p.id_insumo}
                            className={`border-t border-gray-50 ${i % 2 === 0 ? '' : 'bg-gray-50/50'}`}>
                            <td className="px-3 py-2 font-medium text-gray-800">{p.insumo}</td>
                            <td className="px-3 py-2 text-right text-gray-500">{p.stock_actual}</td>
                            <td className="px-3 py-2 text-right text-gray-500">{p.necesario.toFixed(2)}</td>
                            <td className="px-3 py-2 text-right font-bold text-indigo-700">{p.cantidad_pedido.toFixed(2)}</td>
                            <td className="px-3 py-2 text-right text-gray-400">{p.unidad}</td>
                            <td className="px-3 py-2 text-right text-orange-600 font-medium">S/ {p.costo_estimado.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
