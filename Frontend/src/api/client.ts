import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': import.meta.env.VITE_API_KEY_READONLY || 'readonly-key-change-in-production',
  },
  timeout: 30000,
})

// Admin client for write operations (upload, pipeline trigger)
const adminClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': import.meta.env.VITE_API_KEY_ADMIN || 'admin-secret-key-change-in-production',
  },
  timeout: 120000,
})

// Response interceptor: extract data, handle errors uniformly
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail ?? error.message
    return Promise.reject(new Error(message))
  }
)

adminClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail ?? error.message
    return Promise.reject(new Error(message))
  }
)

export { apiClient, adminClient }
