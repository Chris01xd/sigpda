import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Languages } from 'lucide-react'
import { IDIOMAS_SOPORTADOS, Idioma } from '../i18n/i18n'

const ETIQUETAS: Record<Idioma, string> = {
  es: 'Español',
  en: 'English',
  zh: '中文',
}

const BANDERAS: Record<Idioma, string> = {
  es: '🇪🇸',
  en: '🇺🇸',
  zh: '🇨🇳',
}

interface LanguageSwitcherProps {
  /** 'oscuro' para fondos oscuros (Sidebar), 'claro' para fondos blancos (Login) */
  variante?: 'oscuro' | 'claro'
}

export default function LanguageSwitcher({ variante = 'oscuro' }: LanguageSwitcherProps) {
  const { i18n, t } = useTranslation()
  const [abierto, setAbierto] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const actual = (i18n.language?.split('-')[0] as Idioma) || 'es'

  useEffect(() => {
    const alHacerClicFuera = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false)
    }
    document.addEventListener('mousedown', alHacerClicFuera)
    return () => document.removeEventListener('mousedown', alHacerClicFuera)
  }, [])

  const cambiarIdioma = (idioma: Idioma) => {
    i18n.changeLanguage(idioma)
    setAbierto(false)
  }

  const estiloBoton =
    variante === 'oscuro'
      ? 'w-full text-primary-200 hover:bg-primary-800 hover:text-white'
      : 'text-gray-500 hover:bg-gray-100 hover:text-gray-800 border border-gray-200'

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setAbierto((v) => !v)}
        title={t('sidebar.idioma')}
        className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors ${estiloBoton}`}
      >
        <Languages className="w-4 h-4" />
        <span>{BANDERAS[actual]} {ETIQUETAS[actual]}</span>
      </button>

      {abierto && (
        <div
          className={`absolute ${variante === 'oscuro' ? 'bottom-full left-0 mb-1' : 'top-full mt-1 left-1/2 -translate-x-1/2'} w-40 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden z-30`}
        >
          {IDIOMAS_SOPORTADOS.map((idioma) => (
            <button
              key={idioma}
              onClick={() => cambiarIdioma(idioma)}
              className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors ${
                idioma === actual ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span>{BANDERAS[idioma]}</span>
              <span>{ETIQUETAS[idioma]}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
