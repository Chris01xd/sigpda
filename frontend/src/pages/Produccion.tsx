import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus } from 'lucide-react'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Produccion, Plato } from '../types'

const empty = { id_plato: 0, fecha: '', cantidad_preparada: 0, cantidad_vendida: 0, cantidad_sobrante: 0, observaciones: '' }

export default function ProduccionPage() {
  const { t } = useTranslation('produccion')
  const { t: tc } = useTranslation('common')
  const [producciones, setProducciones] = useState<Produccion[]>([])
  const [platos, setPlatos] = useState<Plato[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<typeof empty>(empty)

  useEffect(() => {
    load()
    api.get('/platos').then((r) => setPlatos(r.data))
  }, [])
  const load = () => api.get('/produccion').then((r) => setProducciones(r.data))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await api.post('/produccion', { ...form, fecha: form.fecha || undefined })
    setShowForm(false); setForm(empty); load()
  }

  const columns = [
    { key: 'fecha', header: t('tabla.fecha') },
    { key: 'plato', header: t('tabla.plato') },
    { key: 'cantidad_preparada', header: t('tabla.preparado') },
    { key: 'cantidad_vendida', header: t('tabla.vendido') },
    {
      key: 'cantidad_sobrante', header: t('tabla.sobrante'),
      render: (r: Produccion) => (
        <span className={r.cantidad_sobrante > 0 ? 'text-orange-600 font-medium' : ''}>
          {r.cantidad_sobrante}
        </span>
      ),
    },
    { key: 'observaciones', header: t('tabla.observaciones') },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{t('titulo')}</h1>
          <p className="text-sm text-gray-500">{t('subtitulo')}</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> {t('registrar')}
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={producciones as unknown as Record<string, unknown>[]} />
      </div>
      {showForm && (
        <Modal title={t('registrar')} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.plato')}</label>
                <select required value={form.id_plato} onChange={(e) => setForm({ ...form, id_plato: +e.target.value })} className="input-field">
                  <option value={0}>{t('formulario.seleccionar')}</option>
                  {platos.map((p) => <option key={p.id_plato} value={p.id_plato}>{p.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.fecha')}</label>
                <input type="date" value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.cantidad_preparada')}</label>
                <input type="number" required min={1} value={form.cantidad_preparada} onChange={(e) => setForm({ ...form, cantidad_preparada: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.cantidad_vendida')}</label>
                <input type="number" min={0} value={form.cantidad_vendida} onChange={(e) => setForm({ ...form, cantidad_vendida: +e.target.value })} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.cantidad_sobrante')}</label>
                <input type="number" min={0} value={form.cantidad_sobrante} onChange={(e) => setForm({ ...form, cantidad_sobrante: +e.target.value })} className="input-field" />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('formulario.observaciones')}</label>
                <textarea value={form.observaciones} onChange={(e) => setForm({ ...form, observaciones: e.target.value })} className="input-field h-16 resize-none" />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">{tc('acciones.cancelar')}</button>
              <button type="submit" className="btn-primary">{tc('acciones.guardar')}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
