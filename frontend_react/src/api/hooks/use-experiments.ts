import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { endpoints } from '@/api/endpoints'
import type { Experiment } from '@/types/experiment'
import type { PaginatedResponse } from '@/types/api'

interface UseExperimentsParams {
  limit?: number
  offset?: number
  sortBy?: string
  descending?: boolean
  search?: string
  filters?: string
}

function buildQuery(params: UseExperimentsParams): string {
  const parts: string[] = []
  if (params.limit !== undefined) parts.push(`limit=${params.limit}`)
  if (params.offset !== undefined) parts.push(`offset=${params.offset}`)
  if (params.sortBy) parts.push(`ordering=${params.descending ? '-' : ''}${params.sortBy}`)
  if (params.search) parts.push(`search=${params.search}`)
  if (params.filters) parts.push(params.filters)
  return parts.join('&')
}

export function useExperiments(params: UseExperimentsParams = {}) {
  return useQuery({
    queryKey: ['experiments', params],
    queryFn: async () => {
      const query = buildQuery(params)
      const { data } = await api.get<PaginatedResponse<Experiment> | Experiment[]>(
        `${endpoints.experiments}?${query}`,
      )
      if ('results' in data) return data
      return { count: data.length, next: null, previous: null, results: data }
    },
  })
}

export function useExperiment(name: string) {
  return useQuery({
    queryKey: ['experiment', name],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Experiment> | Experiment[]>(
        `${endpoints.experiments}?name=${name}`,
      )
      const results = 'results' in data ? data.results : data
      return results[0] ?? null
    },
    enabled: !!name,
  })
}

export interface ExperimentDashboardItem {
  name: string
  ulid: string
  successful_run_count: number
  failed_run_count: number
}

export interface ExperimentDashboardSummary {
  total_experiments: number
  total_runs: number
  total_successful: number
  total_failed: number
  success_rate: number
}

export interface ExperimentDashboardResponse {
  experiments: ExperimentDashboardItem[]
  summary: ExperimentDashboardSummary
}

export function useExperimentDashboard(filters?: string, enabled = true) {
  return useQuery({
    queryKey: ['experiment-dashboard', filters],
    queryFn: async () => {
      const query = filters ? `?${filters}` : ''
      const { data } = await api.get<ExperimentDashboardResponse>(
        `${endpoints.experimentDashboard}${query}`,
      )
      return data
    },
    enabled,
  })
}

export function useExperimentFilterOptions(filters?: string) {
  return useQuery({
    queryKey: ['experiment-filter-options', filters],
    queryFn: async () => {
      const query = filters ? `?${filters}` : ''
      const { data } = await api.get(`${endpoints.filterOptions('experiment')}${query}`)
      return data
    },
  })
}
