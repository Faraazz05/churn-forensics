import { useQuery } from '@tanstack/react-query'
import { getPrediction, getBatchPredictions } from '../api/predict'

export const usePredict = (customerId: string) => {
  return useQuery({
    queryKey: ['predict', customerId],
    queryFn: () => getPrediction(customerId),
    enabled: !!customerId,
  })
}

export const useBatchPredictions = () => {
  return useQuery({
    queryKey: ['predict', 'batch'],
    queryFn: () => getBatchPredictions(),
  })
}
