import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { endpoints } from '@/api/endpoints'
import type { Environment } from '@/types/experiment'
import type { PaginatedResponse } from '@/types/api'

interface UseEnvironmentsParams {
  limit?: number
  offset?: number
  sortBy?: string
  descending?: boolean
  search?: string
  filters?: string
}

function buildQuery(params: UseEnvironmentsParams): string {
  const parts: string[] = []
  if (params.limit !== undefined) parts.push(`limit=${params.limit}`)
  if (params.offset !== undefined) parts.push(`offset=${params.offset}`)
  if (params.sortBy) parts.push(`ordering=${params.descending ? '-' : ''}${params.sortBy}`)
  if (params.search) parts.push(`search=${params.search}`)
  if (params.filters) parts.push(params.filters)
  return parts.join('&')
}

export function useEnvironments(params: UseEnvironmentsParams = {}) {
  return useQuery({
    queryKey: ['environments', params],
    queryFn: async () => {
      const query = buildQuery(params)
      const { data } = await api.get<PaginatedResponse<Environment> | Environment[]>(
        `${endpoints.environments}?${query}`,
      )
      if ('results' in data) return data
      return { count: data.length, next: null, previous: null, results: data }
    },
  })
}

export function useEnvironment(name: string) {
  return useQuery({
    queryKey: ['environment', name],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Environment> | Environment[]>(
        `${endpoints.environments}?name=${name}`,
      )
      const results = 'results' in data ? data.results : data
      return results[0] ?? null
    },
    enabled: !!name,
  })
}
