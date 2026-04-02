import { apiClient } from './client'
import { SegmentsResponse, SegmentOut } from '../types/api'

export const getSegments = async (filters: Record<string, any> = {}): Promise<SegmentsResponse> => {
  const params = new URLSearchParams(filters)
  return apiClient.get(`/segments?${params.toString()}`)
}

export const getSegmentDetails = async (segmentId: string): Promise<SegmentOut> => {
  return apiClient.get(`/segments/${segmentId}`)
}
