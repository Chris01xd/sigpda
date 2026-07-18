import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Interceptor de request: siempre lee el token del localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor de response: solo redirige al login en 401 (excluye el propio endpoint de login)
let ya_redirigiendo = false
api.interceptors.response.use(
  (res) => res,
  (error) => {
    const es_login = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !ya_redirigiendo && !es_login) {
      ya_redirigiendo = true
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.replace('/login')
      setTimeout(() => { ya_redirigiendo = false }, 3000)
    }
    return Promise.reject(error)
  }
)

export default api
