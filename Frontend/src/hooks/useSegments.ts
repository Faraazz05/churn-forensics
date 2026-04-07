import { useQuery } from '@tanstack/react-query'
import { getSegments, getSegmentDetails, getTrends } from '../api/segments'

export const useSegments = (filters: Record<string, any> = {}) => {
  return useQuery({
    queryKey: ['segments', filters],
    queryFn: () => getSegments(filters),
  })
}

export const useSegmentDetails = (segmentId: string) => {
  return useQuery({
    queryKey: ['segments', 'detail', segmentId],
    queryFn: () => getSegmentDetails(segmentId),
    enabled: !!segmentId,
  })
}

export const useTrends = () => {
  return useQuery({
    queryKey: ['segments', 'trends'],
    queryFn: () => getTrends(),
  })
}
