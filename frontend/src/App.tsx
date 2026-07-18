import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import PrivateRoute from './components/PrivateRoute'
import Layout from './components/Layout'

import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Ventas from './pages/Ventas'
import Produccion from './pages/Produccion'
import Desperdicio from './pages/Desperdicio'
import Platos from './pages/Platos'
import Insumos from './pages/Insumos'
import Recetas from './pages/Recetas'
import Clientes from './pages/Clientes'
import Proveedores from './pages/Proveedores'
import Restaurantes from './pages/Restaurantes'
import Usuarios from './pages/Usuarios'
import Recomendaciones from './pages/Recomendaciones'
import IA from './pages/IA'
import Estadisticas from './pages/Estadisticas'
import Bitacora from './pages/Bitacora'
import Configuracion from './pages/Configuracion'
import AlertasInteligentes from './pages/AlertasInteligentes'
import Sostenibilidad from './pages/Sostenibilidad'
import Reportes from './pages/Reportes'
import Pedidos from './pages/Pedidos'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard"     element={<Dashboard />} />
            <Route path="ventas"        element={<Ventas />} />
            <Route path="produccion"    element={<Produccion />} />
            <Route path="desperdicio"   element={<Desperdicio />} />
            <Route path="platos"        element={<Platos />} />
            <Route path="insumos"       element={<Insumos />} />
            <Route path="recetas"       element={<Recetas />} />
            <Route path="clientes"      element={<Clientes />} />
            <Route path="proveedores"   element={<Proveedores />} />
            <Route path="restaurantes"  element={<Restaurantes />} />
            <Route path="usuarios"      element={<Usuarios />} />
            <Route path="recomendaciones" element={<Recomendaciones />} />
            <Route path="ia"            element={<IA />} />
            <Route path="estadisticas"  element={<Estadisticas />} />
            <Route path="bitacora"      element={<Bitacora />} />
            <Route path="configuracion"        element={<Configuracion />} />
            <Route path="alertas-inteligentes" element={<AlertasInteligentes />} />
            <Route path="sostenibilidad"       element={<Sostenibilidad />} />
            <Route path="reportes"             element={<Reportes />} />
            <Route path="pedidos"              element={<Pedidos />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
