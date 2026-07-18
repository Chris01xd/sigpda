import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 ml-64 overflow-y-auto">
        <div className="p-6 min-h-screen">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
