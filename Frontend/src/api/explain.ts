import { apiClient } from './client'
import { ExplanationOut } from '../types/api'

export const getExplanation = async (customerId: string): Promise<ExplanationOut> => {
  return apiClient.get(`/explain/${customerId}`)
}

export const getGlobalExplanations = async (): Promise<any> => {
  return apiClient.get('/explain/global')
}
