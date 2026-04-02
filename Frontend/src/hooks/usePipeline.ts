import { useQuery, useMutation } from '@tanstack/react-query'
import { runPipeline, getPipelineStatus } from '../api/pipeline'

export const usePipelineRun = () => {
  return useMutation({
    mutationFn: () => runPipeline(),
  })
}

export const usePipelineStatus = (runId: string) => {
  return useQuery({
    queryKey: ['pipeline', 'status', runId],
    queryFn: () => getPipelineStatus(runId),
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state?.data?.status;
      if (status === 'queued' || status === 'running') {
        return 2000;
      }
      return false;
    },
  })
}
