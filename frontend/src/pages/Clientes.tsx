import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Cliente } from '../types'

const empty = { nombre: '', tipo_documento: 'DNI', numero_documento: '', direccion: '', telefono: '', correo: '', estado: true }

export default function Clientes() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Cliente | null>(null)
  const [form, setForm] = useState<typeof empty>(empty)

  useEffect(() => { load() }, [])
  const load = () => api.get('/clientes').then((r) => setClientes(r.data))

  const openEdit = (c: Cliente) => { setEditing(c); setForm({ ...empty, ...c }); setShowForm(true) }
  const openNew = () => { setEditing(null); setForm(empty); setShowForm(true) }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editing) await api.put(`/clientes/${editing.id_cliente}`, form)
    else await api.post('/clientes', form)
    setShowForm(false); load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('¿Eliminar cliente?')) return
    await api.delete(`/clientes/${id}`); load()
  }

  const columns = [
    { key: 'nombre', header: 'Nombre' },
    { key: 'tipo_documento', header: 'Tipo Doc.' },
    { key: 'numero_documento', header: 'Documento' },
    { key: 'telefono', header: 'Teléfono' },
    { key: 'correo', header: 'Correo' },
    {
      key: 'acciones', header: '',
      render: (r: Cliente) => (
        <div className="flex gap-1">
          <button onClick={() => openEdit(r)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"><Pencil className="w-3.5 h-3.5" /></button>
          <button onClick={() => handleDelete(r.id_cliente)} className="p-1.5 text-red-500 hover:bg-red-50 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Clientes</h1>
          <p className="text-sm text-gray-500">Base de datos de clientes</p>
        </div>
        <button onClick={openNew} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuevo Cliente
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={clientes as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title={editing ? 'Editar Cliente' : 'Nuevo Cliente'} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo *</label>
                <input required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo documento</label>
                <select value={form.tipo_documento} onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })} className="input-field">
                  <option value="DNI">DNI</option>
                  <option value="RUC">RUC</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">N° Documento *</label>
                <input required value={form.numero_documento} onChange={(e) => setForm({ ...form, numero_documento: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
                <input value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Correo</label>
                <input type="email" value={form.correo} onChange={(e) => setForm({ ...form, correo: e.target.value })} className="input-field" />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Dirección</label>
                <input value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} className="input-field" />
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
