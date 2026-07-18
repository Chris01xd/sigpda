import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShoppingCart, Trash2, AlertTriangle, TrendingUp, BellRing, Gauge } from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts'
import api from '../api/client'
import StatCard from '../components/StatCard'

const COLORS = ['#6366f1', '#f43f5e', '#f59e0b', '#10b981', '#3b82f6']

interface AlertaResumen {
  id_alerta: number
  tipo_alerta: string
  nivel_riesgo: string
  titulo: string
  descripcion: string
  plato?: string
  insumo?: string
}

const NIVEL_STYLE: Record<string, string> = {
  CRITICO: 'bg-red-50 border-red-300 text-red-700',
  ALTO:    'bg-orange-50 border-orange-300 text-orange-700',
  MEDIO:   'bg-yellow-50 border-yellow-200 text-yellow-700',
  BAJO:    'bg-blue-50 border-blue-200 text-blue-700',
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [kpis, setKpis] = useState<Record<string, number>>({})
  const [ventas, setVentas] = useState<{ fecha: string; total: number }[]>([])
  const [desperdicios, setDesperdicios] = useState<{ motivo: string; costo: number }[]>([])
  const [topPlatos, setTopPlatos] = useState<{ plato: string; vendidos: number }[]>([])
  const [alertas, setAlertas] = useState<AlertaResumen[]>([])
  const [eficiencia, setEficiencia] = useState<any>(null)

  useEffect(() => {
    api.get('/dashboard/kpis').then((r) => setKpis(r.data))
    api.get('/dashboard/ventas-recientes').then((r) => setVentas(r.data))
    api.get('/dashboard/desperdicio-por-motivo').then((r) => setDesperdicios(r.data))
    api.get('/dashboard/top-platos').then((r) => setTopPlatos(r.data))
    api.get('/alertas-inteligentes?limit=8&estado=pendiente').then((r) => setAlertas(r.data)).catch(() => {})
    api.get('/dashboard/eficiencia').then((r) => setEficiencia(r.data)).catch(() => {})
  }, [])

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-sm text-gray-500">Resumen del sistema en tiempo real</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
        <StatCard
          title="Ventas este mes"
          value={`S/ ${(kpis.ventas_mes || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })}`}
          icon={<TrendingUp className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Ventas hoy"
          value={kpis.num_ventas_hoy || 0}
          subtitle="transacciones"
          icon={<ShoppingCart className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Costo desperdicio (mes)"
          value={`S/ ${(kpis.costo_desperdicio_mes || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })}`}
          icon={<Trash2 className="w-6 h-6" />}
          color="red"
        />
        <StatCard
          title="Stock crítico"
          value={kpis.stock_critico || 0}
          subtitle="insumos bajo mínimo"
          icon={<AlertTriangle className="w-6 h-6" />}
          color="yellow"
        />
        <StatCard
          title="Alertas críticas"
          value={kpis.alertas_criticas || 0}
          subtitle="pendientes de atención"
          icon={<BellRing className="w-6 h-6" />}
          color="red"
        />
      </div>

      {/* Semáforo de eficiencia */}
      {eficiencia && (() => {
        const colorMap: Record<string, { bg: string; text: string; bar: string; emoji: string }> = {
          verde:    { bg: 'bg-green-50  border-green-200',  text: 'text-green-700',  bar: 'bg-green-500',  emoji: '🟢' },
          amarillo: { bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-700', bar: 'bg-yellow-400', emoji: '🟡' },
          rojo:     { bg: 'bg-red-50    border-red-200',    text: 'text-red-700',    bar: 'bg-red-500',    emoji: '🔴' },
        }
        const c = colorMap[eficiencia.color] ?? colorMap.amarillo
        const comp = eficiencia.componentes
        return (
          <div className={`card mb-6 border ${c.bg}`}>
            <div className="flex flex-col sm:flex-row sm:items-center gap-6 p-2">
              <div className="flex items-center gap-4 shrink-0">
                <Gauge className={`w-6 h-6 ${c.text}`} />
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Índice de Eficiencia Operativa</p>
                  <p className={`text-4xl font-bold ${c.text}`}>
                    {eficiencia.indice}<span className="text-lg font-normal">/100</span>
                  </p>
                </div>
                <span className={`text-2xl`}>{c.emoji}</span>
              </div>
              <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { label: 'Producción', key: 'produccion', peso: 40 },
                  { label: 'Alertas',    key: 'alertas',    peso: 30 },
                  { label: 'Desperdicio',key: 'desperdicio',peso: 30 },
                ].map(({ label, key, peso }) => {
                  const v = comp[key]
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-600 font-medium">{label} <span className="text-gray-400">({peso}%)</span></span>
                        <span className="font-semibold text-gray-700">{v.puntaje}</span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${c.bar}`} style={{ width: `${v.puntaje}%` }} />
                      </div>
                      <p className="text-xs text-gray-400 mt-1 truncate">{v.detalle}</p>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )
      })()}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        <div className="xl:col-span-2 card">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Ventas últimos 30 días</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={ventas}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="fecha" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [`S/ ${Number(v).toFixed(2)}`, 'Total']} />
              <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Desperdicio por motivo</h2>
          {desperdicios.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={desperdicios} dataKey="costo" nameKey="motivo" cx="50%" cy="50%" outerRadius={70} label={false}>
                  {desperdicios.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => [`S/ ${Number(v).toFixed(2)}`, 'Costo']} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-gray-400 text-sm">
              Sin datos de desperdicio
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 card">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Top 10 platos más vendidos</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={topPlatos} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis dataKey="plato" type="category" tick={{ fontSize: 11 }} width={120} />
              <Tooltip />
              <Bar dataKey="vendidos" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-700 flex items-center gap-2">
              <BellRing className="w-4 h-4 text-orange-500" /> Alertas inteligentes
            </h2>
            <button
              onClick={() => navigate('/alertas-inteligentes')}
              className="text-xs text-primary-600 hover:underline"
            >
              Ver todas
            </button>
          </div>
          {alertas.length === 0 ? (
            <p className="text-sm text-gray-400">Sin alertas pendientes</p>
          ) : (
            <div className="space-y-2 max-h-[220px] overflow-y-auto">
              {alertas.map((a) => (
                <div
                  key={a.id_alerta}
                  className={`p-3 rounded-lg text-sm border ${NIVEL_STYLE[a.nivel_riesgo] ?? 'bg-gray-50 border-gray-200'}`}
                >
                  <p className="font-medium leading-tight">{a.titulo}</p>
                  <p className="text-xs mt-0.5 opacity-80 line-clamp-1">{a.descripcion}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
