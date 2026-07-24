import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'

interface UsuarioRow {
  id_usuario: number
  nombre: string
  apellido: string
  usuario: string
  correo: string
  rol: string
  id_rol: number
  estado: boolean
}
interface Rol { id_rol: number; nombre: string }

const empty = { nombre: '', apellido: '', correo: '', usuario: '', contrasena: '', id_rol: 1, estado: true }

export default function Usuarios() {
  const { t } = useTranslation(['usuarios', 'common'])
  const [usuarios, setUsuarios] = useState<UsuarioRow[]>([])
  const [roles, setRoles] = useState<Rol[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<UsuarioRow | null>(null)
  const [form, setForm] = useState<typeof empty>(empty)

  useEffect(() => {
    load()
    api.get('/roles').then((r) => setRoles(r.data))
  }, [])
  const load = () => api.get('/usuarios').then((r) => setUsuarios(r.data))

  const openEdit = (u: UsuarioRow) => {
    setEditing(u)
    setForm({ ...empty, ...u, contrasena: '' })
    setShowForm(true)
  }
  const openNew = () => { setEditing(null); setForm(empty); setShowForm(true) }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const body = editing
      ? { nombre: form.nombre, apellido: form.apellido, correo: form.correo, id_rol: form.id_rol, estado: form.estado, nueva_contrasena: form.contrasena || undefined }
      : form
    if (editing) await api.put(`/usuarios/${editing.id_usuario}`, body)
    else await api.post('/usuarios', body)
    setShowForm(false); load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('confirmar_eliminar'))) return
    await api.delete(`/usuarios/${id}`); load()
  }

  const columns = [
    { key: 'nombre', header: t('tabla.nombre'), render: (r: UsuarioRow) => `${r.nombre} ${r.apellido}` },
    { key: 'usuario', header: t('tabla.usuario') },
    { key: 'correo', header: t('tabla.correo') },
    { key: 'rol', header: t('tabla.rol') },
    {
      key: 'estado', header: t('tabla.estado'),
      render: (r: UsuarioRow) => (
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${r.estado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {r.estado ? t('estado.activo', { ns: 'common' }) : t('estado.inactivo', { ns: 'common' })}
        </span>
      ),
    },
    {
      key: 'acciones', header: '',
      render: (r: UsuarioRow) => (
        <div className="flex gap-1">
          <button onClick={() => openEdit(r)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"><Pencil className="w-3.5 h-3.5" /></button>
          <button onClick={() => handleDelete(r.id_usuario)} className="p-1.5 text-red-500 hover:bg-red-50 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
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
          <Plus className="w-4 h-4" /> {t('nuevo_usuario')}
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={usuarios as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title={editing ? t('modal.editar_titulo') : t('modal.nuevo_titulo')} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.nombre')}</label>
                <input required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.apellido')}</label>
                <input required value={form.apellido} onChange={(e) => setForm({ ...form, apellido: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.usuario')}</label>
                <input required disabled={!!editing} value={form.usuario} onChange={(e) => setForm({ ...form, usuario: e.target.value })} className="input-field disabled:bg-gray-100" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.correo')}</label>
                <input required type="email" value={form.correo} onChange={(e) => setForm({ ...form, correo: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{editing ? t('formulario.nueva_contrasena') : t('formulario.contrasena')}</label>
                <input required={!editing} type="password" value={form.contrasena} onChange={(e) => setForm({ ...form, contrasena: e.target.value })} className="input-field" placeholder={editing ? t('formulario.contrasena_placeholder_editar') : ''} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.rol')}</label>
                <select value={form.id_rol} onChange={(e) => setForm({ ...form, id_rol: +e.target.value })} className="input-field">
                  {roles.map((r) => <option key={r.id_rol} value={r.id_rol}>{r.nombre}</option>)}
                </select>
              </div>
              {editing && (
                <div className="flex items-center gap-2 col-span-2">
                  <input type="checkbox" id="estado" checked={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.checked })} />
                  <label htmlFor="estado" className="text-sm text-gray-700">{t('formulario.usuario_activo')}</label>
                </div>
              )}
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
