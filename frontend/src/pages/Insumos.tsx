import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2, AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Insumo } from '../types'

const UNIDADES = ['kg', 'g', 'lt', 'ml', 'unidad', 'porción', 'atado', 'bandeja']

const empty = { id_restaurante: null, id_proveedor: null, nombre: '', categoria: '', unidad_medida: 'kg', stock_disponible: 0, stock_minimo: 0, costo_unitario: 0, fecha_vencimiento: '', proveedor: '', estado: true }

export default function Insumos() {
  const { t } = useTranslation(['insumos', 'common'])
  const [insumos, setInsumos] = useState<Insumo[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Insumo | null>(null)
  const [form, setForm] = useState<typeof empty>(empty)

  useEffect(() => { load() }, [])
  const load = () => api.get('/insumos').then((r) => setInsumos(r.data))

  const openEdit = (i: Insumo) => {
    setEditing(i)
    setForm({ ...empty, ...i, fecha_vencimiento: i.fecha_vencimiento || '' })
    setShowForm(true)
  }

  const openNew = () => { setEditing(null); setForm(empty); setShowForm(true) }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const body = { ...form, fecha_vencimiento: form.fecha_vencimiento || null }
    if (editing) await api.put(`/insumos/${editing.id_insumo}`, body)
    else await api.post('/insumos', body)
    setShowForm(false); load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('confirmar_eliminar'))) return
    await api.delete(`/insumos/${id}`); load()
  }

  const columns = [
    { key: 'nombre', header: t('tabla.nombre') },
    { key: 'categoria', header: t('tabla.categoria') },
    {
      key: 'stock_disponible', header: t('tabla.stock'),
      render: (r: Insumo) => (
        <span className={`font-medium ${r.stock_critico ? 'text-red-600' : 'text-gray-700'}`}>
          {r.stock_critico && <AlertTriangle className="w-3.5 h-3.5 inline mr-1" />}
          {r.stock_disponible} {r.unidad_medida}
        </span>
      ),
    },
    { key: 'stock_minimo', header: t('tabla.minimo'), render: (r: Insumo) => `${r.stock_minimo} ${r.unidad_medida}` },
    { key: 'costo_unitario', header: t('tabla.costo_unitario'), render: (r: Insumo) => `S/ ${r.costo_unitario.toFixed(2)}` },
    { key: 'fecha_vencimiento', header: t('tabla.vencimiento'), render: (r: Insumo) => r.fecha_vencimiento || '—' },
    {
      key: 'acciones', header: '',
      render: (r: Insumo) => (
        <div className="flex gap-1">
          <button onClick={() => openEdit(r)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"><Pencil className="w-3.5 h-3.5" /></button>
          <button onClick={() => handleDelete(r.id_insumo)} className="p-1.5 text-red-500 hover:bg-red-50 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
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

      {insumos.filter((i) => i.stock_critico).length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700">
            <strong>{insumos.filter((i) => i.stock_critico).length}</strong> {t('aviso_stock_critico')}
          </p>
        </div>
      )}

      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={insumos as unknown as Record<string, unknown>[]} />
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
                <input value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })} className="input-field" placeholder={t('formulario.categoria_placeholder')} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.unidad_medida')} *</label>
                <select required value={form.unidad_medida} onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })} className="input-field">
                  {UNIDADES.map((u) => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.stock_disponible')}</label>
                <input type="number" step="0.001" value={form.stock_disponible} onChange={(e) => setForm({ ...form, stock_disponible: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.stock_minimo')}</label>
                <input type="number" step="0.001" value={form.stock_minimo} onChange={(e) => setForm({ ...form, stock_minimo: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.costo_unitario')}</label>
                <input type="number" step="0.01" value={form.costo_unitario} onChange={(e) => setForm({ ...form, costo_unitario: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.fecha_vencimiento')}</label>
                <input type="date" value={form.fecha_vencimiento} onChange={(e) => setForm({ ...form, fecha_vencimiento: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.proveedor')}</label>
                <input value={form.proveedor || ''} onChange={(e) => setForm({ ...form, proveedor: e.target.value })} className="input-field" />
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
