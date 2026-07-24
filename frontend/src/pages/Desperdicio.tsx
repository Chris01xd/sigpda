import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Desperdicio, Plato, Insumo } from '../types'

const MOTIVOS = ['sobreproducción', 'vencimiento', 'mala conservación', 'baja demanda', 'error operativo']
const UNIDADES = ['kg', 'g', 'lt', 'ml', 'unidad', 'porción']

const empty = { tipo: 'plato', id_plato: 0, id_insumo: 0, fecha: '', cantidad: 0, unidad_medida: 'kg', motivo: MOTIVOS[0], costo_estimado: 0, observaciones: '' }

export default function DesperdicioPage() {
  const { t } = useTranslation(['desperdicio', 'common'])
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
    { key: 'fecha', header: t('tabla.fecha') },
    { key: 'tipo', header: t('tabla.tipo') },
    {
      key: 'item', header: t('tabla.item'),
      render: (r: Desperdicio) => r.plato || r.insumo || '—',
    },
    { key: 'motivo', header: t('tabla.motivo') },
    { key: 'cantidad', header: t('tabla.cantidad'), render: (r: Desperdicio) => `${r.cantidad} ${r.unidad_medida}` },
    {
      key: 'costo_estimado', header: t('tabla.costo'),
      render: (r: Desperdicio) => <span className="text-red-600 font-medium">S/ {r.costo_estimado.toFixed(2)}</span>,
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{t('titulo')}</h1>
          <p className="text-sm text-gray-500">{t('subtitulo')}</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> {t('boton_registrar')}
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={desperdicios as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title={t('modal.titulo')} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.tipo')} *</label>
                <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="input-field">
                  <option value="plato">{t('formulario.opcion_plato')}</option>
                  <option value="insumo">{t('formulario.opcion_insumo')}</option>
                </select>
              </div>
              <div>
                {form.tipo === 'plato' ? (
                  <>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.plato')}</label>
                    <select value={form.id_plato} onChange={(e) => setForm({ ...form, id_plato: +e.target.value })} className="input-field">
                      <option value={0}>{t('formulario.seleccionar')}</option>
                      {platos.map((p) => <option key={p.id_plato} value={p.id_plato}>{p.nombre}</option>)}
                    </select>
                  </>
                ) : (
                  <>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.insumo')}</label>
                    <select value={form.id_insumo} onChange={(e) => setForm({ ...form, id_insumo: +e.target.value })} className="input-field">
                      <option value={0}>{t('formulario.seleccionar')}</option>
                      {insumos.map((i) => <option key={i.id_insumo} value={i.id_insumo}>{i.nombre}</option>)}
                    </select>
                  </>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.fecha')}</label>
                <input type="date" value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.motivo')} *</label>
                <select required value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} className="input-field">
                  {MOTIVOS.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.cantidad')} *</label>
                <input type="number" step="0.001" required min={0.001} value={form.cantidad} onChange={(e) => setForm({ ...form, cantidad: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.unidad_medida')}</label>
                <select value={form.unidad_medida} onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })} className="input-field">
                  {UNIDADES.map((u) => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.costo_estimado')}</label>
                <input type="number" step="0.01" min={0} value={form.costo_estimado} onChange={(e) => setForm({ ...form, costo_estimado: +e.target.value })} className="input-field" />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.observaciones')}</label>
                <textarea value={form.observaciones} onChange={(e) => setForm({ ...form, observaciones: e.target.value })} className="input-field h-16 resize-none" />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">{t('acciones.cancelar', { ns: 'common' })}</button>
              <button type="submit" className="btn-primary">{t('acciones.guardar', { ns: 'common' })}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
