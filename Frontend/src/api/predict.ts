import { apiClient } from './client'
import { PredictionOut, BatchPredictionOut } from '../types/api'

export const getPrediction = async (customerId: string): Promise<PredictionOut> => {
  return apiClient.get(`/predict/${customerId}`)
}

export const getBatchPredictions = async (): Promise<BatchPredictionOut> => {
  return apiClient.get('/predict/batch')
}
