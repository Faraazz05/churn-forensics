import { apiClient } from './client'
import { CustomerRiskOut, WatchlistResponse, CustomerProfileOut } from '../types/api'

export const getCustomerRisk = async (threshold?: number): Promise<CustomerRiskOut[]> => {
  const url = threshold !== undefined ? `/customers/risk?threshold=${threshold}` : '/customers/risk'
  return apiClient.get(url)
}

export const getCustomer = async (id: string): Promise<CustomerProfileOut> => {
  return apiClient.get(`/customers/${id}`)
}

export const getWatchlist = async (threshold?: number): Promise<WatchlistResponse> => {
  const url = threshold !== undefined ? `/watchlist?threshold=${threshold}` : '/watchlist'
  return apiClient.get(url)
}
