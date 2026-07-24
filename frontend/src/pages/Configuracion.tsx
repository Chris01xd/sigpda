import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Save, CheckCircle2, Send, XCircle } from 'lucide-react'
import api from '../api/client'

interface ConfigRow { id_configuracion: number; clave: string; valor: string; descripcion: string }

export default function Configuracion() {
  const { t } = useTranslation('configuracion')
  const [configs, setConfigs] = useState<ConfigRow[]>([])
  const [editValues, setEditValues] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState(false)
  const [testResult, setTestResult]   = useState<{ ok: boolean; mensaje: string } | null>(null)
  const [testing, setTesting]         = useState(false)
  const [waResult, setWaResult]       = useState<{ ok: boolean; mensaje: string } | null>(null)
  const [waTesting, setWaTesting]     = useState(false)

  useEffect(() => {
    api.get('/configuracion').then((r) => {
      setConfigs(r.data)
      const vals: Record<string, string> = {}
      r.data.forEach((c: ConfigRow) => { vals[c.clave] = c.valor || '' })
      setEditValues(vals)
    })
  }, [])

  const handleSave = async (clave: string) => {
    await api.put('/configuracion', { clave, valor: editValues[clave] })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleTestWhatsApp = async () => {
    setWaTesting(true)
    setWaResult(null)
    try {
      const r = await api.post('/configuracion/probar-whatsapp')
      setWaResult(r.data)
    } catch (e: any) {
      setWaResult({ ok: false, mensaje: e?.response?.data?.detail ?? t('whatsapp.error_generico') })
    } finally {
      setWaTesting(false)
    }
  }

  const handleTestEmail = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const r = await api.post('/configuracion/probar-email')
      setTestResult(r.data)
    } catch (e: any) {
      setTestResult({ ok: false, mensaje: e?.response?.data?.detail ?? t('email.error_generico') })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{t('titulo')}</h1>
        <p className="text-sm text-gray-500">{t('subtitulo')}</p>
      </div>

      {saved && (
        <div className="mb-4 bg-green-50 border border-green-200 rounded-xl p-3 flex items-center gap-2 text-green-700 text-sm">
          <CheckCircle2 className="w-4 h-4" /> {t('guardado_correctamente')}
        </div>
      )}

      <div className="card">
        <div className="divide-y divide-gray-100">
          {configs.map((c) => (
            <>
              <div key={c.clave} className="py-4 flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-800">{t(`etiquetas.${c.clave}`, { defaultValue: c.clave })}</p>
                  {c.descripcion && <p className="text-xs text-gray-500 mt-0.5">{c.descripcion}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <input
                    value={editValues[c.clave] || ''}
                    onChange={(e) => setEditValues({ ...editValues, [c.clave]: e.target.value })}
                    className="input-field w-48"
                    type={c.clave === 'notif_email_password' || c.clave === 'notif_twilio_token' ? 'password' : 'text'}
                  />
                  <button
                    onClick={() => handleSave(c.clave)}
                    className="btn-primary flex items-center gap-1.5 py-1.5 px-3 text-sm"
                  >
                    <Save className="w-3.5 h-3.5" /> {t('guardar')}
                  </button>
                </div>
              </div>
              {c.clave === 'notif_twilio_numero' && (
                <div key="test-wa-row" className="py-4 flex flex-col gap-2">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleTestWhatsApp}
                      disabled={waTesting}
                      className="btn-primary flex items-center gap-1.5 py-1.5 px-4 text-sm disabled:opacity-60 bg-green-600 hover:bg-green-700"
                    >
                      <Send className="w-3.5 h-3.5" />
                      {waTesting ? t('whatsapp.enviando') : t('whatsapp.probar')}
                    </button>
                    <p className="text-xs text-gray-400">{t('whatsapp.descripcion')}</p>
                  </div>
                  {waResult && (
                    <div className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${waResult.ok ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'}`}>
                      {waResult.ok
                        ? <CheckCircle2 className="w-4 h-4 shrink-0" />
                        : <XCircle className="w-4 h-4 shrink-0" />}
                      {waResult.mensaje}
                    </div>
                  )}
                </div>
              )}
              {c.clave === 'notif_email_password' && (
                <div key="test-email-row" className="py-4 flex flex-col gap-2">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleTestEmail}
                      disabled={testing}
                      className="btn-primary flex items-center gap-1.5 py-1.5 px-4 text-sm disabled:opacity-60"
                    >
                      <Send className="w-3.5 h-3.5" />
                      {testing ? t('email.enviando') : t('email.probar')}
                    </button>
                    <p className="text-xs text-gray-400">{t('email.descripcion')}</p>
                  </div>
                  {testResult && (
                    <div className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${testResult.ok ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'}`}>
                      {testResult.ok
                        ? <CheckCircle2 className="w-4 h-4 shrink-0" />
                        : <XCircle className="w-4 h-4 shrink-0" />}
                      {testResult.mensaje}
                    </div>
                  )}
                </div>
              )}
            </>
          ))}
          {configs.length === 0 && (
            <p className="py-8 text-center text-gray-400 text-sm">{t('sin_configuraciones')}</p>
          )}
        </div>
      </div>
    </div>
  )
}
