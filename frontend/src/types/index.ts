export interface User {
  id: number
  nombre: string
  apellido: string
  usuario: string
  correo: string
  rol: string
  permisos: Record<string, string[]>
}

export interface AuthState {
  user: User | null
  token: string | null
}

export interface Restaurante {
  id_restaurante: number
  nombre_comercial: string
  ruc?: string
  direccion?: string
  distrito?: string
  provincia?: string
  responsable?: string
  telefono?: string
  correo?: string
  estado: boolean
}

export interface Cliente {
  id_cliente: number
  nombre: string
  tipo_documento: string
  numero_documento: string
  direccion?: string
  telefono?: string
  correo?: string
  estado: boolean
}

export interface Proveedor {
  id_proveedor: number
  nombre: string
  tipo_documento: string
  numero_documento: string
  contacto?: string
  telefono?: string
  correo?: string
  direccion?: string
  estado: boolean
}

export interface Plato {
  id_plato: number
  nombre: string
  categoria?: string
  descripcion?: string
  precio_venta: number
  costo_estimado: number
  tiempo_preparacion_min: number
  estado: boolean
}

export interface Insumo {
  id_insumo: number
  nombre: string
  categoria?: string
  unidad_medida: string
  stock_disponible: number
  stock_minimo: number
  costo_unitario: number
  fecha_vencimiento?: string
  proveedor?: string
  estado: boolean
  stock_critico: boolean
}

export interface DetalleVenta {
  id_plato: number
  plato: string
  cantidad: number
  precio_unitario: number
  subtotal: number
}

export interface Venta {
  id_venta: number
  fecha?: string
  hora?: string
  total: number
  metodo_pago: string
  tipo_comprobante: string
  numero_comprobante?: string
  cliente_nombre?: string
  detalles: DetalleVenta[]
}

export interface Produccion {
  id_produccion: number
  id_plato: number
  plato: string
  fecha?: string
  cantidad_preparada: number
  cantidad_vendida: number
  cantidad_sobrante: number
  observaciones?: string
}

export interface Desperdicio {
  id_desperdicio: number
  plato?: string
  insumo?: string
  fecha?: string
  tipo: string
  cantidad: number
  unidad_medida: string
  motivo: string
  costo_estimado: number
  observaciones?: string
}

export interface Receta {
  id_receta: number
  id_plato: number
  plato: string
  id_insumo: number
  insumo: string
  cantidad_usada: number
  unidad_medida?: string
}

export interface Recomendacion {
  tipo: string
  severidad: string
  titulo: string
  descripcion: string
  modulo: string
}
