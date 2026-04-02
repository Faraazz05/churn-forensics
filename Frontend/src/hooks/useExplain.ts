import { useQuery } from '@tanstack/react-query'
import { getExplanation, getGlobalExplanations } from '../api/explain'

export const useExplain = (customerId: string) => {
  return useQuery({
    queryKey: ['explain', customerId],
    queryFn: () => getExplanation(customerId),
    enabled: !!customerId,
  })
}

export const useGlobalExplain = () => {
  return useQuery({
    queryKey: ['explain', 'global'],
    queryFn: () => getGlobalExplanations(),
  })
}
