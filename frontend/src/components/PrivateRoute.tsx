import { Navigate } from 'react-router-dom'

// Lee directamente de localStorage — sin depender de estado React
// para evitar problemas de timing entre setState y navigate
export default function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  return token ? <>{children}</> : <Navigate to="/login" replace />
}
