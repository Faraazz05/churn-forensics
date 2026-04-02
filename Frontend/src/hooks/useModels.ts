import { useQuery } from '@tanstack/react-query'
import { getModelsLeaderboard } from '../api/models'

export const useModels = () => {
  return useQuery({
    queryKey: ['models', 'leaderboard'],
    queryFn: () => getModelsLeaderboard(),
  })
}
