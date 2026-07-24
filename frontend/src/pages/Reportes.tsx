import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FileDown, FileText, CheckCircle2, XCircle } from 'lucide-react'
import api from '../api/client'

export default function Reportes() {
  const { t } = useTranslation('reportes')
  const [loading, setLoading]   = useState(false)
  const [estado,  setEstado]    = useState<'idle' | 'ok' | 'error'>('idle')
  const [mensaje, setMensaje]   = useState('')

  const descargarPDF = async () => {
    setLoading(true)
    setEstado('idle')
    try {
      const r = await api.get('/reportes/semanal', { responseType: 'blob' })
      const url  = URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      const hoy  = new Date().toISOString().slice(0, 10).replace(/-/g, '')
      link.href     = url
      link.download = `SIGPDA_Reporte_${hoy}.pdf`
      link.click()
      URL.revokeObjectURL(url)
      setEstado('ok')
      setMensaje(t('descargado_ok'))
    } catch {
      setEstado('error')
      setMensaje(t('error_generar'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <FileText className="w-6 h-6 text-indigo-600" />
          {t('titulo')}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {t('subtitulo')}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Reporte semanal */}
        <div className="card p-6 flex flex-col gap-4">
          <div className="flex items-start gap-4">
            <div className="bg-indigo-100 rounded-xl p-3 shrink-0">
              <FileDown className="w-7 h-7 text-indigo-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-800 text-base">{t('semanal.titulo')}</h2>
              <p className="text-sm text-gray-500 mt-1">
                {t('semanal.descripcion')}
              </p>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 space-y-1">
            <p>✓ {t('semanal.items.resumen')}</p>
            <p>✓ {t('semanal.items.huella')}</p>
            <p>✓ {t('semanal.items.top_desperdicio')}</p>
            <p>✓ {t('semanal.items.ahorro')}</p>
            <p>✓ {t('semanal.items.alertas')}</p>
            <p>✓ {t('semanal.items.recomendaciones')}</p>
          </div>

          {estado === 'ok' && (
            <div className="flex items-center gap-2 text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm">
              <CheckCircle2 className="w-4 h-4 shrink-0" /> {mensaje}
            </div>
          )}
          {estado === 'error' && (
            <div className="flex items-center gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">
              <XCircle className="w-4 h-4 shrink-0" /> {mensaje}
            </div>
          )}

          <button
            onClick={descargarPDF}
            disabled={loading}
            className="btn-primary flex items-center justify-center gap-2 py-2.5 disabled:opacity-60"
          >
            <FileDown className="w-4 h-4" />
            {loading ? t('semanal.generando') : t('semanal.descargar')}
          </button>
        </div>

        {/* Info */}
        <div className="card p-6 bg-indigo-50 border border-indigo-100">
          <h3 className="font-semibold text-indigo-800 mb-3">{t('info.titulo')}</h3>
          <div className="space-y-3 text-sm text-indigo-700">
            <p>
              <span className="font-medium">{t('info.dueno_label')}</span> {t('info.dueno_texto')}
            </p>
            <p>
              <span className="font-medium">{t('info.auditorias_label')}</span> {t('info.auditorias_texto')}
            </p>
            <p>
              <span className="font-medium">{t('info.tesis_label')}</span> {t('info.tesis_texto')}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
