import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import LanguageSwitcher from './LanguageSwitcher'
import {
  LayoutDashboard, Users, Building2, UserCheck, Truck,
  UtensilsCrossed, Package, BookOpen, ShoppingCart,
  Factory, Trash2, TrendingUp, BarChart3, ScrollText,
  Settings, Lightbulb, Brain, LogOut, ChefHat, BellRing,
  Leaf, FileText, ShoppingBag,
} from 'lucide-react'

const allMenuItems = [
  { path: '/dashboard', labelKey: 'nav.dashboard', icon: LayoutDashboard, modulo: 'dashboard' },
  { path: '/ventas', labelKey: 'nav.ventas', icon: ShoppingCart, modulo: 'ventas' },
  { path: '/produccion', labelKey: 'nav.produccion', icon: Factory, modulo: 'produccion' },
  { path: '/desperdicio', labelKey: 'nav.desperdicio', icon: Trash2, modulo: 'desperdicio' },
  { path: '/platos', labelKey: 'nav.platos', icon: UtensilsCrossed, modulo: 'platos' },
  { path: '/insumos', labelKey: 'nav.insumos', icon: Package, modulo: 'insumos' },
  { path: '/recetas', labelKey: 'nav.recetas', icon: BookOpen, modulo: 'recetas' },
  { path: '/clientes', labelKey: 'nav.clientes', icon: UserCheck, modulo: 'clientes' },
  { path: '/proveedores', labelKey: 'nav.proveedores', icon: Truck, modulo: 'proveedores' },
  { path: '/restaurantes', labelKey: 'nav.restaurantes', icon: Building2, modulo: 'restaurantes' },
  { path: '/usuarios', labelKey: 'nav.usuarios', icon: Users, modulo: 'usuarios' },
  { path: '/recomendaciones', labelKey: 'nav.recomendaciones', icon: Lightbulb, modulo: 'prediccion' },
  { path: '/ia', labelKey: 'nav.ia', icon: Brain, modulo: 'prediccion' },
  { path: '/alertas-inteligentes', labelKey: 'nav.alertas_inteligentes', icon: BellRing, modulo: 'prediccion' },
  { path: '/estadisticas', labelKey: 'nav.estadisticas', icon: BarChart3, modulo: 'estadisticas' },
  { path: '/bitacora', labelKey: 'nav.bitacora', icon: ScrollText, modulo: 'bitacora' },
  { path: '/pedidos',        labelKey: 'nav.pedidos',        icon: ShoppingBag, modulo: 'prediccion'  },
  { path: '/sostenibilidad', labelKey: 'nav.sostenibilidad', icon: Leaf,        modulo: 'estadisticas' },
  { path: '/reportes',       labelKey: 'nav.reportes',   icon: FileText,    modulo: 'estadisticas' },
  { path: '/configuracion',  labelKey: 'nav.configuracion',  icon: Settings,  modulo: 'configuracion' },
]

export default function Sidebar() {
  const { user, logout, hasPermission } = useAuth()
  const { t } = useTranslation()

  const visibleItems = allMenuItems.filter((item) => hasPermission(item.modulo, 'ver'))

  return (
    <aside className="w-64 bg-primary-900 text-white flex flex-col h-screen fixed left-0 top-0 z-20">
      <div className="p-4 border-b border-primary-700 flex items-center gap-3">
        <div className="bg-primary-600 rounded-lg p-2">
          <ChefHat className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-sm font-bold leading-tight">{t('app.nombre')}</h1>
          <p className="text-xs text-primary-300">{t('app.version')}</p>
        </div>
      </div>

      {user && (
        <div className="p-4 border-b border-primary-700">
          <p className="text-sm font-medium truncate">{user.nombre} {user.apellido}</p>
          <span className="text-xs bg-primary-600 text-primary-100 px-2 py-0.5 rounded-full">
            {user.rol}
          </span>
        </div>
      )}

      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {visibleItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm mb-1 transition-colors ${
                isActive
                  ? 'bg-primary-600 text-white font-medium'
                  : 'text-primary-200 hover:bg-primary-800 hover:text-white'
              }`
            }
          >
            <item.icon className="w-4 h-4 flex-shrink-0" />
            {t(item.labelKey)}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-primary-700 space-y-1">
        <LanguageSwitcher />
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-primary-200 hover:bg-primary-800 hover:text-white rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          {t('sidebar.cerrar_sesion')}
        </button>
      </div>
    </aside>
  )
}
