import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Proveedor } from '../types'

const empty = { nombre: '', tipo_documento: 'RUC', numero_documento: '', contacto: '', telefono: '', correo: '', direccion: '', estado: true }

export default function Proveedores() {
  const { t } = useTranslation('proveedores')
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Proveedor | null>(null)
  const [form, setForm] = useState<typeof empty>(empty)

  useEffect(() => { load() }, [])
  const load = () => api.get('/proveedores').then((r) => setProveedores(r.data))

  const openEdit = (p: Proveedor) => { setEditing(p); setForm({ ...empty, ...p }); setShowForm(true) }
  const openNew = () => { setEditing(null); setForm(empty); setShowForm(true) }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editing) await api.put(`/proveedores/${editing.id_proveedor}`, form)
    else await api.post('/proveedores', form)
    setShowForm(false); load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('confirmar_eliminar'))) return
    await api.delete(`/proveedores/${id}`); load()
  }

  const columns = [
    { key: 'nombre', header: t('tabla.nombre') },
    { key: 'tipo_documento', header: t('tabla.tipo_documento') },
    { key: 'numero_documento', header: t('tabla.numero_documento') },
    { key: 'contacto', header: t('tabla.contacto') },
    { key: 'telefono', header: t('tabla.telefono') },
    { key: 'correo', header: t('tabla.correo') },
    {
      key: 'acciones', header: '',
      render: (r: Proveedor) => (
        <div className="flex gap-1">
          <button onClick={() => openEdit(r)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"><Pencil className="w-3.5 h-3.5" /></button>
          <button onClick={() => handleDelete(r.id_proveedor)} className="p-1.5 text-red-500 hover:bg-red-50 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
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
          <Plus className="w-4 h-4" /> {t('nuevo_proveedor')}
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={proveedores as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title={editing ? t('modal.editar_titulo') : t('modal.nuevo_titulo')} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.nombre')}</label>
                <input required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.tipo_documento')}</label>
                <select value={form.tipo_documento} onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })} className="input-field">
                  <option value="RUC">RUC</option>
                  <option value="DNI">DNI</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.numero_documento')}</label>
                <input required value={form.numero_documento} onChange={(e) => setForm({ ...form, numero_documento: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.contacto')}</label>
                <input value={form.contacto} onChange={(e) => setForm({ ...form, contacto: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.telefono')}</label>
                <input value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.correo')}</label>
                <input type="email" value={form.correo} onChange={(e) => setForm({ ...form, correo: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.direccion')}</label>
                <input value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} className="input-field" />
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
