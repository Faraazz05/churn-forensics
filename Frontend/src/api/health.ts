import { apiClient } from './client'
import { HealthResponse } from '../types/api'

export const checkHealth = async (): Promise<HealthResponse> => {
  return apiClient.get('/health')
}
