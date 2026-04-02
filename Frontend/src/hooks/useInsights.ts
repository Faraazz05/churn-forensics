import { useQuery, useMutation } from '@tanstack/react-query'
import { getInsights, askQuestion } from '../api/insights'

export const useInsightsData = () => {
  return useQuery({
    queryKey: ['insights', 'report'],
    queryFn: () => getInsights(),
  })
}

export const useAgentQA = () => {
  return useMutation({
    mutationFn: (question: string) => askQuestion(question),
  })
}
