import { apiClient } from './client'
import { DriftResponse, DriftFeatureOut } from '../types/api'

export const getDriftReport = async (): Promise<DriftResponse> => {
  return apiClient.get('/drift')
}

export const getDriftFeatures = async (): Promise<DriftFeatureOut[]> => {
  return apiClient.get('/drift/features')
}

export const getDriftWarnings = async (): Promise<DriftFeatureOut[]> => {
  return apiClient.get('/drift/warnings')
}
