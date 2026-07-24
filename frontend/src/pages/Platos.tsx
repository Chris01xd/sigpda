import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Plato } from '../types'

const CATEGORIAS = ['Entrada', 'Plato de fondo', 'Sopa', 'Postre', 'Bebida', 'Especialidad regional', 'Combo']

const empty = { id_restaurante: null, nombre: '', categoria: '', descripcion: '', precio_venta: 0, costo_estimado: 0, tiempo_preparacion_min: 0, estado: true }

export default function Platos() {
  const { t } = useTranslation(['platos', 'common'])
  const [platos, setPlatos] = useState<Plato[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Plato | null>(null)
  const [form, setForm] = useState<typeof empty>(empty)

  useEffect(() => { load() }, [])
  const load = () => api.get('/platos').then((r) => setPlatos(r.data))

  const openEdit = (p: Plato) => { setEditing(p); setForm({ ...empty, ...p }); setShowForm(true) }
  const openNew = () => { setEditing(null); setForm(empty); setShowForm(true) }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editing) await api.put(`/platos/${editing.id_plato}`, form)
    else await api.post('/platos', form)
    setShowForm(false); load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('confirmar_eliminar'))) return
    await api.delete(`/platos/${id}`); load()
  }

  const columns = [
    { key: 'nombre', header: t('tabla.nombre') },
    { key: 'categoria', header: t('tabla.categoria') },
    { key: 'precio_venta', header: t('tabla.precio'), render: (r: Plato) => <span className="font-medium text-green-700">S/ {r.precio_venta.toFixed(2)}</span> },
    { key: 'costo_estimado', header: t('tabla.costo'), render: (r: Plato) => `S/ ${r.costo_estimado.toFixed(2)}` },
    { key: 'tiempo_preparacion_min', header: t('tabla.tiempo') },
    {
      key: 'acciones', header: '',
      render: (r: Plato) => (
        <div className="flex gap-1">
          <button onClick={() => openEdit(r)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"><Pencil className="w-3.5 h-3.5" /></button>
          <button onClick={() => handleDelete(r.id_plato)} className="p-1.5 text-red-500 hover:bg-red-50 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{t('titulo')}</h1>
          <p className="text-sm text-gray-500">{t('subtitulo')}</p>
        </div>
        <button onClick={openNew} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> {t('boton_nuevo')}
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={platos as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title={editing ? t('modal.editar') : t('modal.nuevo')} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.nombre')} *</label>
                <input required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.categoria')}</label>
                <select value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })} className="input-field">
                  <option value="">{t('formulario.seleccionar')}</option>
                  {CATEGORIAS.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.precio_venta')}</label>
                <input type="number" step="0.01" required value={form.precio_venta} onChange={(e) => setForm({ ...form, precio_venta: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.costo_estimado')}</label>
                <input type="number" step="0.01" value={form.costo_estimado} onChange={(e) => setForm({ ...form, costo_estimado: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.tiempo_preparacion')}</label>
                <input type="number" value={form.tiempo_preparacion_min} onChange={(e) => setForm({ ...form, tiempo_preparacion_min: +e.target.value })} className="input-field" />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.descripcion')}</label>
                <textarea value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} className="input-field h-20 resize-none" />
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
