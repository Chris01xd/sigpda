import { NavLink } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard, Users, Building2, UserCheck, Truck,
  UtensilsCrossed, Package, BookOpen, ShoppingCart,
  Factory, Trash2, TrendingUp, BarChart3, ScrollText,
  Settings, Lightbulb, Brain, LogOut, ChefHat, BellRing,
  Leaf, FileText, ShoppingBag,
} from 'lucide-react'

const allMenuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, modulo: 'dashboard' },
  { path: '/ventas', label: 'Ventas', icon: ShoppingCart, modulo: 'ventas' },
  { path: '/produccion', label: 'Producción', icon: Factory, modulo: 'produccion' },
  { path: '/desperdicio', label: 'Desperdicio', icon: Trash2, modulo: 'desperdicio' },
  { path: '/platos', label: 'Platos', icon: UtensilsCrossed, modulo: 'platos' },
  { path: '/insumos', label: 'Insumos', icon: Package, modulo: 'insumos' },
  { path: '/recetas', label: 'Recetas', icon: BookOpen, modulo: 'recetas' },
  { path: '/clientes', label: 'Clientes', icon: UserCheck, modulo: 'clientes' },
  { path: '/proveedores', label: 'Proveedores', icon: Truck, modulo: 'proveedores' },
  { path: '/restaurantes', label: 'Restaurantes', icon: Building2, modulo: 'restaurantes' },
  { path: '/usuarios', label: 'Usuarios', icon: Users, modulo: 'usuarios' },
  { path: '/recomendaciones', label: 'Recomendaciones', icon: Lightbulb, modulo: 'prediccion' },
  { path: '/ia', label: 'IA / Predicciones', icon: Brain, modulo: 'prediccion' },
  { path: '/alertas-inteligentes', label: 'Alertas Inteligentes', icon: BellRing, modulo: 'prediccion' },
  { path: '/estadisticas', label: 'Estadísticas', icon: BarChart3, modulo: 'estadisticas' },
  { path: '/bitacora', label: 'Bitácora', icon: ScrollText, modulo: 'bitacora' },
  { path: '/pedidos',        label: 'Pedidos',        icon: ShoppingBag, modulo: 'prediccion'  },
  { path: '/sostenibilidad', label: 'Sostenibilidad', icon: Leaf,        modulo: 'estadisticas' },
  { path: '/reportes',       label: 'Reportes PDF',   icon: FileText,    modulo: 'estadisticas' },
  { path: '/configuracion',  label: 'Configuración',  icon: Settings,  modulo: 'configuracion' },
]

export default function Sidebar() {
  const { user, logout, hasPermission } = useAuth()

  const visibleItems = allMenuItems.filter((item) => hasPermission(item.modulo, 'ver'))

  return (
    <aside className="w-64 bg-primary-900 text-white flex flex-col h-screen fixed left-0 top-0 z-20">
      <div className="p-4 border-b border-primary-700 flex items-center gap-3">
        <div className="bg-primary-600 rounded-lg p-2">
          <ChefHat className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-sm font-bold leading-tight">SIGPDA</h1>
          <p className="text-xs text-primary-300">v2.0</p>
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
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-primary-700">
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-primary-200 hover:bg-primary-800 hover:text-white rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
