import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { MessageCircle, X, Send, Mic, Volume2, VolumeX, Loader2 } from 'lucide-react'
import api from '../api/client'
import { ChatMensaje } from '../types'

const SpeechRecognitionCtor: any =
  (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
const reconocimientoDisponible = !!SpeechRecognitionCtor
const sintesisDisponible = 'speechSynthesis' in window

const CODIGO_VOZ: Record<string, string> = {
  es: 'es-PE',
  en: 'en-US',
  zh: 'zh-CN',
}

export default function ChatbotFlotante() {
  const { t, i18n } = useTranslation('chatbot')
  const idioma = (i18n.language?.split('-')[0]) || 'es'
  const codigoVoz = CODIGO_VOZ[idioma] || 'es-PE'

  const [abierto, setAbierto] = useState(false)
  const [mensajes, setMensajes] = useState<ChatMensaje[]>([
    { rol: 'assistant', contenido: t('saludo_inicial') },
  ])
  const [texto, setTexto] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const [escuchando, setEscuchando] = useState(false)
  const [vozActiva, setVozActiva] = useState(true)

  const listaRef = useRef<HTMLDivElement>(null)
  const reconocimientoRef = useRef<any>(null)

  useEffect(() => {
    listaRef.current?.scrollTo({ top: listaRef.current.scrollHeight, behavior: 'smooth' })
  }, [mensajes, abierto, cargando])

  useEffect(() => {
    return () => {
      reconocimientoRef.current?.stop()
      if (sintesisDisponible) window.speechSynthesis.cancel()
    }
  }, [])

  // Si el usuario aún no ha conversado, refresca el saludo al cambiar de idioma
  useEffect(() => {
    setMensajes((prev) =>
      prev.length === 1 && prev[0].rol === 'assistant'
        ? [{ rol: 'assistant', contenido: t('saludo_inicial') }]
        : prev
    )
  }, [idioma, t])

  const hablar = (texto: string) => {
    if (!sintesisDisponible || !vozActiva) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(texto)
    utterance.lang = codigoVoz
    window.speechSynthesis.speak(utterance)
  }

  const enviarMensaje = async (contenido: string) => {
    const mensaje = contenido.trim()
    if (!mensaje || cargando) return

    const historialPrevio = mensajes
    setMensajes((prev) => [...prev, { rol: 'user', contenido: mensaje }])
    setTexto('')
    setError('')
    setCargando(true)

    try {
      const { data } = await api.post('/chatbot/mensaje', {
        mensaje,
        historial: historialPrevio.slice(-12),
        idioma,
      })
      setMensajes((prev) => [...prev, { rol: 'assistant', contenido: data.respuesta }])
      hablar(data.respuesta)
    } catch (err: any) {
      const detalle = err.response?.data?.detail || t('error_generico')
      setError(detalle)
    } finally {
      setCargando(false)
    }
  }

  const alternarMicrofono = () => {
    if (!reconocimientoDisponible) return

    if (escuchando) {
      reconocimientoRef.current?.stop()
      return
    }

    const reconocimiento = new SpeechRecognitionCtor()
    reconocimiento.lang = codigoVoz
    reconocimiento.interimResults = false
    reconocimiento.maxAlternatives = 1

    reconocimiento.onresult = (evento: any) => {
      const transcripcion = evento.results?.[0]?.[0]?.transcript
      if (transcripcion) enviarMensaje(transcripcion)
    }
    reconocimiento.onerror = () => setEscuchando(false)
    reconocimiento.onend = () => setEscuchando(false)

    reconocimientoRef.current = reconocimiento
    setEscuchando(true)
    reconocimiento.start()
  }

  if (!abierto) {
    return (
      <button
        onClick={() => setAbierto(true)}
        className="fixed bottom-6 right-6 z-50 bg-primary-600 hover:bg-primary-700 text-white rounded-full p-4 shadow-lg transition-colors"
        aria-label={t('abrir') ?? undefined}
      >
        <MessageCircle className="w-6 h-6" />
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-[22rem] max-w-[90vw] h-[32rem] max-h-[80vh] bg-white rounded-xl shadow-2xl flex flex-col border border-gray-200">
      <div className="flex items-center justify-between bg-primary-900 text-white rounded-t-xl px-4 py-3">
        <div>
          <p className="text-sm font-semibold leading-tight">{t('titulo')}</p>
          <p className="text-xs text-primary-300">{t('subtitulo')}</p>
        </div>
        <div className="flex items-center gap-1">
          {sintesisDisponible && (
            <button
              onClick={() => {
                setVozActiva((v) => !v)
                if (vozActiva) window.speechSynthesis.cancel()
              }}
              title={vozActiva ? t('desactivar_voz') ?? undefined : t('activar_voz') ?? undefined}
              className="p-1.5 rounded hover:bg-primary-700 transition-colors"
            >
              {vozActiva ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>
          )}
          <button
            onClick={() => setAbierto(false)}
            title={t('cerrar') ?? undefined}
            className="p-1.5 rounded hover:bg-primary-700 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div ref={listaRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-2 bg-gray-50">
        {mensajes.map((m, i) => (
          <div key={i} className={`flex ${m.rol === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                m.rol === 'user'
                  ? 'bg-primary-600 text-white rounded-br-none'
                  : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none'
              }`}
            >
              {m.contenido}
            </div>
          </div>
        ))}
        {cargando && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg rounded-bl-none px-3 py-2 text-sm text-gray-400 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> {t('pensando')}
            </div>
          </div>
        )}
        {error && (
          <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          enviarMensaje(texto)
        }}
        className="flex items-center gap-1.5 border-t border-gray-200 p-2"
      >
        {reconocimientoDisponible && (
          <button
            type="button"
            onClick={alternarMicrofono}
            title={escuchando ? t('detener_grabacion') ?? undefined : t('hablar') ?? undefined}
            className={`p-2 rounded-lg transition-colors ${
              escuchando ? 'bg-red-100 text-red-600 animate-pulse' : 'text-gray-500 hover:bg-gray-100'
            }`}
          >
            <Mic className="w-4 h-4" />
          </button>
        )}
        <input
          type="text"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder={(escuchando ? t('placeholder_escuchando') : t('placeholder_escribir')) ?? ''}
          disabled={cargando}
          className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <button
          type="submit"
          disabled={cargando || !texto.trim()}
          className="p-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}
