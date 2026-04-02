import { apiClient } from './client'
import { LeaderboardResponse, ModelOut } from '../types/api'

export const getModelsLeaderboard = async (): Promise<LeaderboardResponse> => {
  return apiClient.get('/models')
}

export const getBestModel = async (): Promise<ModelOut | undefined> => {
  const data: LeaderboardResponse = await apiClient.get('/models')
  return data.best_model
}
