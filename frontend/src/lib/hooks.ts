import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getHealth, analyzeRepo, getReport, listReports, compareReports } from './api'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    staleTime: 60_000,
    retry: false,
  })
}

export function useAnalyzeRepo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (url: string) => analyzeRepo(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
  })
}

export function useReport(id: string) {
  return useQuery({
    queryKey: ['report', id],
    queryFn: () => getReport(id),
    enabled: !!id,
  })
}

export function useReports() {
  return useQuery({
    queryKey: ['reports'],
    queryFn: listReports,
  })
}

export function useCompare() {
  return useMutation({
    mutationFn: (data: { report_id_a: string; report_id_b: string }) => compareReports(data),
  })
}
