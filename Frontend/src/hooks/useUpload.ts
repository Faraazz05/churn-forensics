import { useMutation } from '@tanstack/react-query'
import { uploadData } from '../api/upload'

export const useUpload = () => {
  return useMutation({
    mutationFn: (file: File) => uploadData(file),
  })
}
