import { useQuery } from '@tanstack/react-query'
import { getDriftReport, getDriftWarnings, getDriftFeatures } from '../api/drift'

export const useDriftReport = () => {
  return useQuery({
    queryKey: ['drift', 'report'],
    queryFn: () => getDriftReport(),
  })
}

export const useDriftWarnings = () => {
  return useQuery({
    queryKey: ['drift', 'warnings'],
    queryFn: () => getDriftWarnings(),
  })
}

export const useDriftFeatures = () => {
  return useQuery({
    queryKey: ['drift', 'features'],
    queryFn: () => getDriftFeatures(),
  })
}
