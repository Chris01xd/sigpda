import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import DataTable from '../components/DataTable'

interface BitacoraRow {
  id_bitacora: number
  usuario_nombre: string
  rol: string
  modulo: string
  accion: string
  descripcion: string
  fecha: string
  hora: string
  ip_equipo: string
  resultado: string
}

export default function Bitacora() {
  const { t } = useTranslation('bitacora')
  const [registros, setRegistros] = useState<BitacoraRow[]>([])
  const [filtroModulo, setFiltroModulo] = useState('')
  const [filtroResultado, setFiltroResultado] = useState('')

  useEffect(() => { load() }, [filtroModulo, filtroResultado])

  const load = () => {
    const params: Record<string, string> = {}
    if (filtroModulo) params.modulo = filtroModulo
    if (filtroResultado) params.resultado = filtroResultado
    api.get('/bitacora', { params }).then((r) => setRegistros(r.data))
  }

  const columns = [
    { key: 'fecha', header: t('tabla.fecha') },
    { key: 'hora', header: t('tabla.hora') },
    { key: 'usuario_nombre', header: t('tabla.usuario') },
    { key: 'rol', header: t('tabla.rol') },
    { key: 'modulo', header: t('tabla.modulo') },
    { key: 'accion', header: t('tabla.accion') },
    { key: 'descripcion', header: t('tabla.descripcion') },
    {
      key: 'resultado', header: t('tabla.resultado'),
      render: (r: BitacoraRow) => (
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
          r.resultado === 'éxito' ? 'bg-green-100 text-green-700' :
          r.resultado === 'error' ? 'bg-red-100 text-red-700' :
          'bg-yellow-100 text-yellow-700'
        }`}>
          {r.resultado}
        </span>
      ),
    },
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{t('titulo')}</h1>
        <p className="text-sm text-gray-500">{t('subtitulo')}</p>
      </div>

      <div className="card mb-4">
        <div className="flex gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">{t('filtros.modulo')}</label>
            <input
              value={filtroModulo}
              onChange={(e) => setFiltroModulo(e.target.value)}
              className="input-field w-48"
              placeholder={t('filtros.modulo_placeholder')}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">{t('filtros.resultado')}</label>
            <select value={filtroResultado} onChange={(e) => setFiltroResultado(e.target.value)} className="input-field w-40">
              <option value="">{t('filtros.todos')}</option>
              <option value="éxito">{t('filtros.exito')}</option>
              <option value="error">{t('filtros.error')}</option>
              <option value="advertencia">{t('filtros.advertencia')}</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={registros as unknown as Record<string, unknown>[]} />
      </div>
    </div>
  )
}
