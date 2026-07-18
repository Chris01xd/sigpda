import { useState } from 'react'
import { FileDown, FileText, CheckCircle2, XCircle } from 'lucide-react'
import api from '../api/client'

export default function Reportes() {
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
      setMensaje('Reporte descargado correctamente.')
    } catch {
      setEstado('error')
      setMensaje('Error al generar el reporte. Verifica que haya datos registrados.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <FileText className="w-6 h-6 text-indigo-600" />
          Reportes
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Generación de reportes ejecutivos en PDF para dirección y análisis
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
              <h2 className="font-semibold text-gray-800 text-base">Reporte Ejecutivo Semanal</h2>
              <p className="text-sm text-gray-500 mt-1">
                PDF con KPIs del período, huella de carbono e hídrica, top desperdicios por costo,
                ahorro económico comparativo y alertas inteligentes activas.
              </p>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 space-y-1">
            <p>✓ Resumen de la semana (registros y costos)</p>
            <p>✓ Huella ambiental — CO₂, agua, equivalencias</p>
            <p>✓ Top platos con mayor desperdicio</p>
            <p>✓ Ahorro económico vs período anterior</p>
            <p>✓ Alertas inteligentes pendientes</p>
            <p>✓ Recomendaciones operativas</p>
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
            {loading ? 'Generando PDF...' : 'Descargar Reporte PDF'}
          </button>
        </div>

        {/* Info */}
        <div className="card p-6 bg-indigo-50 border border-indigo-100">
          <h3 className="font-semibold text-indigo-800 mb-3">¿Para qué sirve este reporte?</h3>
          <div className="space-y-3 text-sm text-indigo-700">
            <p>
              <span className="font-medium">Para el dueño del restaurante:</span> resumen ejecutivo semanal
              con los indicadores más importantes sin necesidad de ingresar al sistema.
            </p>
            <p>
              <span className="font-medium">Para auditorías:</span> evidencia documentada del
              control del desperdicio alimentario con métricas verificables.
            </p>
            <p>
              <span className="font-medium">Para la tesis:</span> el reporte incluye la huella de carbono
              calculada con factores FAO 2023, alineado con los ODS 12 (Producción y Consumo Responsable).
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
