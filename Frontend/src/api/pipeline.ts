import { adminClient } from './client'
import { PipelineStatusResponse } from '../types/api'

export const runPipeline = async (): Promise<{ run_id: string; status: string; message: string }> => {
  return adminClient.post('/pipeline/run')
}

export const getPipelineStatus = async (runId: string): Promise<PipelineStatusResponse> => {
  return adminClient.get(`/pipeline/status/${runId}`)
}
