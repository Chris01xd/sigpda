import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Desperdicio, Plato, Insumo } from '../types'

const MOTIVOS = ['sobreproducción', 'vencimiento', 'mala conservación', 'baja demanda', 'error operativo']
const UNIDADES = ['kg', 'g', 'lt', 'ml', 'unidad', 'porción']

const empty = { tipo: 'plato', id_plato: 0, id_insumo: 0, fecha: '', cantidad: 0, unidad_medida: 'kg', motivo: MOTIVOS[0], costo_estimado: 0, observaciones: '' }

export default function DesperdicioPage() {
  const [desperdicios, setDesperdicios] = useState<Desperdicio[]>([])
  const [platos, setPlatos] = useState<Plato[]>([])
  const [insumos, setInsumos] = useState<Insumo[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<typeof empty>(empty)

  useEffect(() => {
    load()
    api.get('/platos').then((r) => setPlatos(r.data))
    api.get('/insumos').then((r) => setInsumos(r.data))
  }, [])
  const load = () => api.get('/desperdicio').then((r) => setDesperdicios(r.data))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const body = {
      ...form,
      id_plato: form.tipo === 'plato' ? form.id_plato || null : null,
      id_insumo: form.tipo === 'insumo' ? form.id_insumo || null : null,
      fecha: form.fecha || undefined,
    }
    await api.post('/desperdicio', body)
    setShowForm(false); setForm(empty); load()
  }

  const columns = [
    { key: 'fecha', header: 'Fecha' },
    { key: 'tipo', header: 'Tipo' },
    {
      key: 'item', header: 'Item',
      render: (r: Desperdicio) => r.plato || r.insumo || '—',
    },
    { key: 'motivo', header: 'Motivo' },
    { key: 'cantidad', header: 'Cantidad', render: (r: Desperdicio) => `${r.cantidad} ${r.unidad_medida}` },
    {
      key: 'costo_estimado', header: 'Costo',
      render: (r: Desperdicio) => <span className="text-red-600 font-medium">S/ {r.costo_estimado.toFixed(2)}</span>,
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Desperdicio</h1>
          <p className="text-sm text-gray-500">Registro de mermas y desperdicios</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Registrar Desperdicio
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={desperdicios as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title="Registrar Desperdicio" onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
                <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-field">
                  <option value="plato">Plato</option>
                  <option value="insumo">Insumo</option>
                </select>
              </div>
              <div>
                {form.tipo === 'plato' ? (
                  <>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Plato</label>
                    <select value={form.id_plato} onChange={(e) => setForm({ ...form, id_plato: +e.target.value })} className="input-field">
                      <option value={0}>Seleccionar...</option>
                      {platos.map((p) => <option key={p.id_plato} value={p.id_plato}>{p.nombre}</option>)}
                    </select>
                  </>
                ) : (
                  <>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Insumo</label>
                    <select value={form.id_insumo} onChange={(e) => setForm({ ...form, id_insumo: +e.target.value })} className="input-field">
                      <option value={0}>Seleccionar...</option>
                      {insumos.map((i) => <option key={i.id_insumo} value={i.id_insumo}>{i.nombre}</option>)}
                    </select>
                  </>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
                <input type="date" value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Motivo *</label>
                <select required value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} className="input-field">
                  {MOTIVOS.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cantidad *</label>
                <input type="number" step="0.001" required min={0.001} value={form.cantidad} onChange={(e) => setForm({ ...form, cantidad: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Unidad medida</label>
                <select value={form.unidad_medida} onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })} className="input-field">
                  {UNIDADES.map((u) => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Costo estimado (S/)</label>
                <input type="number" step="0.01" min={0} value={form.costo_estimado} onChange={(e) => setForm({ ...form, costo_estimado: +e.target.value })} className="input-field" />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Observaciones</label>
                <textarea value={form.observaciones} onChange={(e) => setForm({ ...form, observaciones: e.target.value })} className="input-field h-16 resize-none" />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
              <button type="submit" className="btn-primary">Guardar</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
