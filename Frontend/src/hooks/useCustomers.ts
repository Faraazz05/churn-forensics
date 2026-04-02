import { useQuery } from '@tanstack/react-query'
import { getCustomerRisk, getCustomer, getWatchlist } from '../api/customers'

export const useCustomerRisk = (threshold?: number) => {
  return useQuery({
    queryKey: ['customers', 'risk', threshold ?? 'all'],
    queryFn: () => getCustomerRisk(threshold),
  })
}

export const useCustomer = (id: string) => {
  return useQuery({
    queryKey: ['customers', id],
    queryFn: () => getCustomer(id),
    enabled: !!id,
  })
}

export const useWatchlist = (threshold?: number) => {
  return useQuery({
    queryKey: ['watchlist', threshold ?? 'all'],
    queryFn: () => getWatchlist(threshold),
  })
}
