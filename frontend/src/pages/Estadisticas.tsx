import { useEffect, useState } from 'react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import StatCard from '../components/StatCard'
import { TrendingUp, Trash2, ShoppingCart, Package } from 'lucide-react'

export default function Estadisticas() {
  const { t } = useTranslation('estadisticas')
  const [resumen, setResumen] = useState<Record<string, number>>({})
  const [ventasMes, setVentasMes] = useState<{ mes: string; total: number; num: number }[]>([])
  const [desperdicioMes, setDesperdicio] = useState<{ mes: string; costo: number; num: number }[]>([])

  useEffect(() => {
    api.get('/estadisticas/resumen').then((r) => setResumen(r.data))
    api.get('/estadisticas/ventas-por-mes').then((r) => setVentasMes(r.data))
    api.get('/estadisticas/desperdicio-por-mes').then((r) => setDesperdicio(r.data))
  }, [])

  const moneda = (v: number) => `S/ ${v.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{t('titulo')}</h1>
        <p className="text-sm text-gray-500">{t('subtitulo')}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
        <StatCard title={t('kpi.ventas_mes')} value={moneda(resumen.total_ventas_mes || 0)} icon={<TrendingUp className="w-6 h-6" />} color="green" />
        <StatCard title={t('kpi.ventas_anio')} value={moneda(resumen.total_ventas_anio || 0)} icon={<TrendingUp className="w-6 h-6" />} color="blue" />
        <StatCard title={t('kpi.desperdicio_mes')} value={moneda(resumen.total_desperdicio_mes || 0)} icon={<Trash2 className="w-6 h-6" />} color="red" />
        <StatCard title={t('kpi.transacciones_mes')} value={resumen.num_ventas_mes || 0} subtitle={t('kpi.ventas')} icon={<ShoppingCart className="w-6 h-6" />} color="purple" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-base font-semibold text-gray-700 mb-4">{t('graficos.ventas_mensuales')}</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={ventasMes}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [`S/ ${Number(v).toFixed(2)}`, t('graficos.total')]} />
              <Bar dataKey="total" fill="#6366f1" radius={[4, 4, 0, 0]} name={t('graficos.total_ventas')} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-gray-700 mb-4">{t('graficos.costo_desperdicio_mensual')}</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={desperdicioMes}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [`S/ ${Number(v).toFixed(2)}`, t('graficos.costo_desperdicio')]} />
              <Legend />
              <Line type="monotone" dataKey="costo" stroke="#f43f5e" strokeWidth={2} name={t('graficos.costo_desperdicio')} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
