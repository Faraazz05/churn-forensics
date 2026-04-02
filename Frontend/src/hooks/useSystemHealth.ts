import { useQuery } from '@tanstack/react-query'
import { checkHealth } from '../api/health'

export const useSystemHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => checkHealth(),
    refetchInterval: 30000,
  })
}
