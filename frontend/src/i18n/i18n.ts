import i18n, { Resource } from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

export const IDIOMAS_SOPORTADOS = ['es', 'en', 'zh'] as const
export type Idioma = (typeof IDIOMAS_SOPORTADOS)[number]

// Descubre automáticamente todos los archivos de traducción en locales/<idioma>/<namespace>.json
// Así cada página/feature puede agregar su propio namespace sin tocar este archivo.
const modulos = import.meta.glob('./locales/*/*.json', { eager: true }) as Record<
  string,
  { default: Record<string, unknown> }
>

const resources: Resource = {}

for (const ruta in modulos) {
  const coincidencia = ruta.match(/\.\/locales\/([a-zA-Z-]+)\/([a-zA-Z0-9_-]+)\.json$/)
  if (!coincidencia) continue
  const [, idioma, namespace] = coincidencia
  resources[idioma] = resources[idioma] || {}
  resources[idioma][namespace] = modulos[ruta].default
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'es',
    supportedLngs: [...IDIOMAS_SOPORTADOS],
    defaultNS: 'common',
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'sigpda_idioma',
      caches: ['localStorage'],
    },
  })

export default i18n
