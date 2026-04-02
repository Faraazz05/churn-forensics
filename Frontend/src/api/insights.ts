import { apiClient } from './client'
import { InsightResponse, QAResponse } from '../types/api'

export const getInsights = async (): Promise<InsightResponse> => {
  return apiClient.get('/insights')
}

export const askQuestion = async (question: string): Promise<QAResponse> => {
  return apiClient.post('/insights/qa', { question })
}
