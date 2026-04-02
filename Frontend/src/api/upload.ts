import { adminClient } from './client'
import { UploadResponse } from '../types/api'

export const uploadData = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  
  return adminClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
