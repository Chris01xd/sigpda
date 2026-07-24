import { useEffect, useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Receta, Plato, Insumo } from '../types'

const UNIDADES = ['kg', 'g', 'lt', 'ml', 'unidad', 'porción']

export default function Recetas() {
  const { t } = useTranslation(['recetas', 'common'])
  const [recetas, setRecetas] = useState<Receta[]>([])
  const [platos, setPlatos] = useState<Plato[]>([])
  const [insumos, setInsumos] = useState<Insumo[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ id_plato: 0, id_insumo: 0, cantidad_usada: 0, unidad_medida: 'kg' })

  useEffect(() => {
    load()
    api.get('/platos').then((r) => setPlatos(r.data))
    api.get('/insumos').then((r) => setInsumos(r.data))
  }, [])
  const load = () => api.get('/recetas').then((r) => setRecetas(r.data))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await api.post('/recetas', form)
    setShowForm(false); load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('confirmar_eliminar'))) return
    await api.delete(`/recetas/${id}`); load()
  }

  const columns = [
    { key: 'plato', header: t('tabla.plato') },
    { key: 'insumo', header: t('tabla.insumo') },
    { key: 'cantidad_usada', header: t('tabla.cantidad') },
    { key: 'unidad_medida', header: t('tabla.unidad') },
    {
      key: 'acciones', header: '',
      render: (r: Receta) => (
        <button onClick={() => handleDelete(r.id_receta)} className="p-1.5 text-red-500 hover:bg-red-50 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
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
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> {t('boton_agregar')}
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={recetas as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title={t('modal.titulo')} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.plato')} *</label>
              <select required value={form.id_plato} onChange={(e) => setForm({ ...form, id_plato: +e.target.value })} className="input-field">
                <option value={0}>{t('formulario.seleccionar')}</option>
                {platos.map((p) => <option key={p.id_plato} value={p.id_plato}>{p.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.insumo')} *</label>
              <select required value={form.id_insumo} onChange={(e) => setForm({ ...form, id_insumo: +e.target.value })} className="input-field">
                <option value={0}>{t('formulario.seleccionar')}</option>
                {insumos.map((i) => <option key={i.id_insumo} value={i.id_insumo}>{i.nombre}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.cantidad')} *</label>
                <input type="number" step="0.001" required min={0.001} value={form.cantidad_usada} onChange={(e) => setForm({ ...form, cantidad_usada: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.unidad')}</label>
                <select value={form.unidad_medida} onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })} className="input-field">
                  {UNIDADES.map((u) => <option key={u} value={u}>{u}</option>)}
                </select>
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
