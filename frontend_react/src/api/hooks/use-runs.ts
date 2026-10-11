import { useQuery } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { api } from '@/api/client'
import { endpoints } from '@/api/endpoints'
import type { Run } from '@/types/experiment'
import type { PaginatedResponse } from '@/types/api'

interface UseRunsParams {
  limit?: number
  offset?: number
  sortBy?: string
  descending?: boolean
  search?: string
  filters?: string
}

function buildQuery(params: UseRunsParams): string {
  const parts: string[] = []
  if (params.limit !== undefined) parts.push(`limit=${params.limit}`)
  if (params.offset !== undefined) parts.push(`offset=${params.offset}`)
  if (params.sortBy) parts.push(`ordering=${params.descending ? '-' : ''}${params.sortBy}`)
  if (params.search) parts.push(`search=${params.search}`)
  if (params.filters) parts.push(params.filters)
  return parts.join('&')
}

export function useRuns(params: UseRunsParams = {}) {
  return useQuery({
    queryKey: ['runs', params],
    queryFn: async () => {
      const query = buildQuery(params)
      const { data } = await api.get<PaginatedResponse<Run> | Run[]>(
        `${endpoints.runs}?${query}`,
      )
      if ('results' in data) return data
      return { count: data.length, next: null, previous: null, results: data }
    },
  })
}

// The detail endpoint is the only one that serializes `events`; the list
// endpoint deliberately omits them. A 404 maps to null ("Run not found").
export function useRun(ulid: string) {
  return useQuery({
    queryKey: ['run', ulid],
    queryFn: async () => {
      try {
        const { data } = await api.get<Run>(endpoints.run(ulid))
        return data
      } catch (err) {
        if (isAxiosError(err) && err.response?.status === 404) return null
        throw err
      }
    },
    enabled: !!ulid,
  })
}
