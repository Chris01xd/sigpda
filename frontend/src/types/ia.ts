// Tipos del módulo de Inteligencia Artificial (EDA, comparación de modelos, etc.)
// Se mantienen separados de types/index.ts porque son específicos de IA.tsx
// y sus componentes (frontend/src/components/ia/*).

export interface EdaResumen {
  plato: string
  categoria: string
  registros_transacciones: number
  dias_con_venta: number
  dias_cubiertos: number
  fecha_inicio: string | null
  fecha_fin: string | null
}

export interface EdaEstadisticasDescriptivas {
  media?: number
  mediana?: number
  desviacion_estandar?: number
  minimo?: number
  maximo?: number
  q1?: number
  q3?: number
  rango_intercuartilico?: number
}

export interface EdaOutliers {
  cantidad: number
  limite_inferior: number | null
  limite_superior: number | null
  fechas: string[]
}

export interface EdaSeriePunto {
  fecha: string
  cantidad: number
  interpolado: boolean
}

export interface EdaDistribucionBin {
  rango_inicio: number
  rango_fin: number
  frecuencia: number
}

export interface EdaPorDiaSemana {
  dia_semana: string
  demanda_promedio: number
  demanda_total: number
  n: number
}

export interface EdaPorMes {
  mes: string
  demanda_promedio: number
  demanda_total: number
  n: number
}

export interface EdaClimaEvento {
  clima_distribucion?: Record<string, number>
  evento_distribucion?: Record<string, number>
  nota?: string
}

export interface EdaResultado {
  resumen: EdaResumen
  estadisticas_descriptivas: EdaEstadisticasDescriptivas
  valores_faltantes: Record<string, number>
  duplicados: number
  outliers: EdaOutliers
  serie_historica: EdaSeriePunto[]
  distribucion: EdaDistribucionBin[]
  por_dia_semana: EdaPorDiaSemana[]
  por_mes: EdaPorMes[]
  correlaciones: Record<string, Record<string, number | null>>
  clima_evento: EdaClimaEvento
  advertencias: string[]
}

// ─────────────────────────────────────────────────────────────
// Comparación de 5 modelos + validación cruzada + tuning + pruebas
// estadísticas (POST /ia/entrenar-comparar)
// ─────────────────────────────────────────────────────────────

export const NOMBRES_5_MODELOS = [
  'arima', 'prophet', 'holt_winters',
  'transformer_random_forest', 'transformer_gradient_boosting',
] as const

export type NombreModelo5 = typeof NOMBRES_5_MODELOS[number]

export const NOMBRES_5_MODELOS_LEGIBLES: Record<NombreModelo5, string> = {
  arima: 'ARIMA',
  prophet: 'Prophet',
  holt_winters: 'Holt-Winters',
  transformer_random_forest: 'Transformer + Random Forest',
  transformer_gradient_boosting: 'Transformer + Gradient Boosting',
}

export interface MetricasCompletas {
  mae: number | null
  rmse: number | null
  mape: number | null
  smape: number | null
  u_theil: number | null
  r2: number | null
  error?: string
}

export interface FoldCV {
  numero_fold: number
  fecha_inicio_train: string
  fecha_fin_train: string
  fecha_inicio_val: string
  fecha_fin_val: string
  n_train: number
  n_val: number
  mae: number | null
  rmse: number | null
  mape: number | null
  smape: number | null
  u_theil: number | null
  r2: number | null
  tiempo_entrenamiento: number | null
  tiempo_inferencia: number | null
  error?: string
}

export interface ResultadoCV {
  folds: FoldCV[]
  promedio: Record<string, number | null>
  desviacion_estandar: Record<string, number | null>
  minimo: Record<string, number | null>
  maximo: Record<string, number | null>
  tiempo_total: number
  n_folds_ejecutados: number
  n_folds_solicitados: number
  advertencias: string[]
}

export interface ResultadoTuning {
  aplicable: boolean
  motivo?: string
  modelo?: string
  espacio_busqueda?: Record<string, unknown[]>
  combinaciones_evaluadas?: { hiperparametros: Record<string, unknown>; mae: number | null; rmse?: number | null; tiempo: number; error?: string }[]
  n_combinaciones?: number
  mejor_hiperparametros?: Record<string, unknown> | null
  metrica_objetivo?: string
  mejor_valor?: number | null
  tiempo_total?: number
  semilla?: number
  fecha_ejecucion?: string
}

export interface PruebaDM {
  estadistico: number | null
  p_valor: number | null
  significativo: boolean
  interpretacion: string
  modelo_1: string
  modelo_2: string
  modelo_a?: string
  modelo_b?: string
}

export interface PruebaWilcoxon {
  prueba: string
  modelo_a: string
  modelo_b: string
  estadistico: number | null
  p_valor: number | null
  p_valor_ajustado: number | null
  significativo: boolean
  hipotesis: string
  interpretacion: string
  aplicable: boolean
}

export interface PruebaFriedman {
  aplicable: boolean
  estadistico: number | null
  p_valor: number | null
  significativo: boolean
  n_observaciones?: number
  modelos?: string[]
  hipotesis: string
  interpretacion: string
}

export interface EntrenarCompararResultado {
  ejecucion_id: number | null
  estado: string
  dataset: { registros: number; fecha_inicio: string; fecha_fin: string; advertencias: string[] }
  eda_resumen: { resumen: EdaResumen; estadisticas_descriptivas: EdaEstadisticasDescriptivas; advertencias: string[] }
  modelo_ganador: NombreModelo5
  modelo_ganador_legible: string
  mae_ganador: number
  criterio_seleccion: string
  metricas_por_modelo: Record<string, MetricasCompletas>
  info_modelos: Record<string, Record<string, unknown>>
  validacion_cruzada: Record<string, ResultadoCV>
  hiperparametros: Record<string, ResultadoTuning>
  pruebas_estadisticas: {
    friedman: PruebaFriedman
    wilcoxon: PruebaWilcoxon[]
    diebold_mariano: PruebaDM[]
  }
  modelo_guardado: { guardado: boolean; tipo_modelo?: string; fecha?: string; motivo?: string }
  predicciones_futuras: { fecha: string; demanda_estimada: number; recomendacion: number; riesgo: string }[]
  n_datos_entrenamiento: number
  n_datos_prueba: number
  duracion_total_segundos: number
  interpretacion: string[]
}

// ─────────────────────────────────────────────────────────────
// Modelo guardado (GET/POST /ia/modelos-guardados/*)
// ─────────────────────────────────────────────────────────────

export interface ModeloGuardadoMetadata {
  id_plato: number
  nombre_plato: string
  tipo_modelo: string
  tipo_modelo_legible: string
  hiperparametros: Record<string, unknown>
  metricas: MetricasCompletas
  fecha_entrenamiento: string
  rango_temporal_datos: { inicio: string; fin: string }
  n_registros: number
  version_modelo: string
  versiones_librerias: Record<string, string>
  hash_datos: string
  semilla: number
  contexto_prediccion: Record<string, unknown>
}

export interface ModeloVigenteResultado {
  existe: boolean
  vigente: boolean
  metadata: ModeloGuardadoMetadata | null
  recomienda_reentrenar: boolean
  motivo: string
}
