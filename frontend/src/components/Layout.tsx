import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Menu } from 'lucide-react'
import Sidebar from './Sidebar'
import ChatbotFlotante from './ChatbotFlotante'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <main className="flex-1 md:ml-64 w-full overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-center bg-white border-b border-gray-200 p-3 md:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-gray-100"
            aria-label="Abrir menú"
          >
            <Menu className="w-6 h-6 text-gray-700" />
          </button>
        </div>
        <div className="p-6 min-h-screen">
          <Outlet />
        </div>
      </main>
      <ChatbotFlotante />
    </div>
  )
}
