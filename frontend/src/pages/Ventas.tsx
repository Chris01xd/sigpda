import { useEffect, useState } from 'react'
import { Plus, Trash2, Eye } from 'lucide-react'
import api from '../api/client'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Venta, Plato } from '../types'

interface DetallePedido { id_plato: number; nombre: string; precio: number; cantidad: number }

export default function Ventas() {
  const [ventas, setVentas] = useState<Venta[]>([])
  const [platos, setPlatos] = useState<Plato[]>([])
  const [showForm, setShowForm] = useState(false)
  const [detalle, setDetalle] = useState<Venta | null>(null)

  const [pedido, setPedido] = useState<DetallePedido[]>([])
  const [metodo, setMetodo] = useState('efectivo')
  const [comprobante, setComprobante] = useState('ticket')
  const [clienteNombre, setClienteNombre] = useState('')
  const [clienteDoc, setClienteDoc] = useState('')

  useEffect(() => {
    loadVentas()
    api.get('/platos').then((r) => setPlatos(r.data))
  }, [])

  const loadVentas = () => api.get('/ventas').then((r) => setVentas(r.data))

  const addPlato = (plato: Plato) => {
    setPedido((prev) => {
      const existing = prev.find((p) => p.id_plato === plato.id_plato)
      if (existing) return prev.map((p) => p.id_plato === plato.id_plato ? { ...p, cantidad: p.cantidad + 1 } : p)
      return [...prev, { id_plato: plato.id_plato, nombre: plato.nombre, precio: plato.precio_venta, cantidad: 1 }]
    })
  }

  const updateCantidad = (id: number, delta: number) => {
    setPedido((prev) =>
      prev.map((p) => p.id_plato === id ? { ...p, cantidad: Math.max(1, p.cantidad + delta) } : p)
    )
  }

  const removePlato = (id: number) => setPedido((prev) => prev.filter((p) => p.id_plato !== id))
  const total = pedido.reduce((s, p) => s + p.precio * p.cantidad, 0)

  const handleSubmit = async () => {
    if (pedido.length === 0) return alert('Agrega al menos un plato')
    await api.post('/ventas', {
      metodo_pago: metodo,
      tipo_comprobante: comprobante,
      cliente_nombre: clienteNombre || null,
      cliente_documento: clienteDoc || null,
      detalles: pedido.map((p) => ({ id_plato: p.id_plato, cantidad: p.cantidad, precio_unitario: p.precio })),
    })
    setPedido([]); setClienteNombre(''); setClienteDoc(''); setShowForm(false)
    loadVentas()
  }

  const columns = [
    { key: 'id_venta', header: 'N°' },
    { key: 'fecha', header: 'Fecha' },
    { key: 'hora', header: 'Hora' },
    { key: 'tipo_comprobante', header: 'Tipo' },
    { key: 'cliente_nombre', header: 'Cliente' },
    { key: 'metodo_pago', header: 'Pago' },
    {
      key: 'total', header: 'Total',
      render: (r: Venta) => <span className="font-semibold text-green-700">S/ {r.total.toFixed(2)}</span>,
    },
    {
      key: 'acciones', header: '',
      render: (r: Venta) => (
        <button onClick={() => setDetalle(r)} className="text-blue-600 hover:text-blue-800">
          <Eye className="w-4 h-4" />
        </button>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Ventas</h1>
          <p className="text-sm text-gray-500">Registro de transacciones</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nueva Venta
        </button>
      </div>

      <div className="card">
        <DataTable columns={columns as Parameters<typeof DataTable>[0]['columns']} data={ventas as unknown as Record<string, unknown>[]} />
      </div>

      {showForm && (
        <Modal title="Nueva Venta" onClose={() => setShowForm(false)} size="lg">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Método de pago</label>
              <select value={metodo} onChange={(e) => setMetodo(e.target.value)} className="input-field">
                {['efectivo', 'tarjeta', 'yape', 'plin', 'transferencia'].map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Comprobante</label>
              <select value={comprobante} onChange={(e) => setComprobante(e.target.value)} className="input-field">
                {['ticket', 'boleta', 'factura'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cliente (opcional)</label>
              <input value={clienteNombre} onChange={(e) => setClienteNombre(e.target.value)} className="input-field" placeholder="Nombre del cliente" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Documento (opcional)</label>
              <input value={clienteDoc} onChange={(e) => setClienteDoc(e.target.value)} className="input-field" placeholder="DNI / RUC" />
            </div>
          </div>

          <h3 className="font-medium text-gray-700 mb-2">Seleccionar platos</h3>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto mb-4">
            {platos.map((p) => (
              <button
                key={p.id_plato}
                onClick={() => addPlato(p)}
                className="text-left p-3 rounded-lg border border-gray-200 hover:border-primary-400 hover:bg-primary-50 transition-colors"
              >
                <p className="text-sm font-medium truncate">{p.nombre}</p>
                <p className="text-xs text-green-600">S/ {p.precio_venta.toFixed(2)}</p>
              </button>
            ))}
          </div>

          {pedido.length > 0 && (
            <div className="border-t pt-4">
              <h3 className="font-medium text-gray-700 mb-2">Pedido</h3>
              <div className="space-y-2">
                {pedido.map((p) => (
                  <div key={p.id_plato} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                    <span className="text-sm flex-1 truncate">{p.nombre}</span>
                    <div className="flex items-center gap-2 ml-2">
                      <button onClick={() => updateCantidad(p.id_plato, -1)} className="w-6 h-6 rounded-full bg-gray-200 hover:bg-gray-300 text-sm flex items-center justify-center">-</button>
                      <span className="text-sm font-medium w-5 text-center">{p.cantidad}</span>
                      <button onClick={() => updateCantidad(p.id_plato, 1)} className="w-6 h-6 rounded-full bg-gray-200 hover:bg-gray-300 text-sm flex items-center justify-center">+</button>
                      <span className="text-sm text-green-700 w-16 text-right">S/ {(p.precio * p.cantidad).toFixed(2)}</span>
                      <button onClick={() => removePlato(p.id_plato)} className="text-red-400 hover:text-red-600"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-between mt-4 pt-3 border-t">
                <span className="text-lg font-bold">Total: S/ {total.toFixed(2)}</span>
                <button onClick={handleSubmit} className="btn-primary">Registrar Venta</button>
              </div>
            </div>
          )}
        </Modal>
      )}

      {detalle && (
        <Modal title={`Venta N° ${detalle.id_venta}`} onClose={() => setDetalle(null)}>
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <div><span className="text-gray-500">Fecha:</span> {detalle.fecha}</div>
              <div><span className="text-gray-500">Hora:</span> {detalle.hora}</div>
              <div><span className="text-gray-500">Comprobante:</span> {detalle.tipo_comprobante}</div>
              <div><span className="text-gray-500">Pago:</span> {detalle.metodo_pago}</div>
              {detalle.cliente_nombre && <div className="col-span-2"><span className="text-gray-500">Cliente:</span> {detalle.cliente_nombre}</div>}
            </div>
            <table className="w-full text-sm mt-2">
              <thead><tr className="border-b"><th className="text-left py-1">Plato</th><th className="text-right py-1">Cant.</th><th className="text-right py-1">Subtotal</th></tr></thead>
              <tbody>
                {detalle.detalles.map((d, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-1.5">{d.plato}</td>
                    <td className="text-right py-1.5">{d.cantidad}</td>
                    <td className="text-right py-1.5">S/ {d.subtotal.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="flex justify-between font-bold pt-2">
              <span>Total</span>
              <span className="text-green-700">S/ {detalle.total.toFixed(2)}</span>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
