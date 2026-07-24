import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Pencil } from 'lucide-react'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Restaurante } from '../types'

const empty = { nombre_comercial: '', ruc: '', direccion: '', distrito: '', provincia: '', responsable: '', telefono: '', correo: '', estado: true }

export default function Restaurantes() {
  const { t } = useTranslation('restaurantes')
  const [restaurantes, setRestaurantes] = useState<Restaurante[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Restaurante | null>(null)
  const [form, setForm] = useState<typeof empty>(empty)

  useEffect(() => { load() }, [])
  const load = () => api.get('/restaurantes').then((r) => setRestaurantes(r.data))

  const openEdit = (r: Restaurante) => { setEditing(r); setForm({ ...empty, ...r }); setShowForm(true) }
  const openNew = () => { setEditing(null); setForm(empty); setShowForm(true) }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editing) await api.put(`/restaurantes/${editing.id_restaurante}`, form)
    else await api.post('/restaurantes', form)
    setShowForm(false); load()
  }

  const columns = [
    { key: 'nombre_comercial', header: t('tabla.nombre_comercial') },
    { key: 'ruc', header: t('tabla.ruc') },
    { key: 'responsable', header: t('tabla.responsable') },
    { key: 'telefono', header: t('tabla.telefono') },
    { key: 'distrito', header: t('tabla.distrito') },
    {
      key: 'estado', header: t('tabla.estado'),
      render: (r: Restaurante) => (
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${r.estado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {r.estado ? t('estado.activo') : t('estado.inactivo')}
        </span>
      ),
    },
    {
      key: 'acciones', header: '',
      render: (r: Restaurante) => (
        <button onClick={() => openEdit(r)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"><Pencil className="w-3.5 h-3.5" /></button>
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
          <Plus className="w-4 h-4" /> {t('nuevo_restaurante')}
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={restaurantes as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title={editing ? t('modal.editar_titulo') : t('modal.nuevo_titulo')} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.nombre_comercial')}</label>
                <input required value={form.nombre_comercial} onChange={(e) => setForm({ ...form, nombre_comercial: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.ruc')}</label>
                <input value={form.ruc} onChange={(e) => setForm({ ...form, ruc: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.responsable')}</label>
                <input value={form.responsable} onChange={(e) => setForm({ ...form, responsable: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.telefono')}</label>
                <input value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.correo')}</label>
                <input type="email" value={form.correo} onChange={(e) => setForm({ ...form, correo: e.target.value })} className="input-field" />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.direccion')}</label>
                <input value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.distrito')}</label>
                <input value={form.distrito} onChange={(e) => setForm({ ...form, distrito: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.provincia')}</label>
                <input value={form.provincia} onChange={(e) => setForm({ ...form, provincia: e.target.value })} className="input-field" />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">{t('modal.cancelar')}</button>
              <button type="submit" className="btn-primary">{t('modal.guardar')}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
