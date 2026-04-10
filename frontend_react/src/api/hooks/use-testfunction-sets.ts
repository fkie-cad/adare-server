import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { endpoints } from '@/api/endpoints'
import type { TestfunctionSet } from '@/types/experiment'
import type { PaginatedResponse } from '@/types/api'

interface UseTestfunctionSetsParams {
  limit?: number
  offset?: number
  sortBy?: string
  descending?: boolean
  search?: string
  filters?: string
}

function buildQuery(params: UseTestfunctionSetsParams): string {
  const parts: string[] = []
  if (params.limit !== undefined) parts.push(`limit=${params.limit}`)
  if (params.offset !== undefined) parts.push(`offset=${params.offset}`)
  if (params.sortBy) parts.push(`ordering=${params.descending ? '-' : ''}${params.sortBy}`)
  if (params.search) parts.push(`search=${params.search}`)
  if (params.filters) parts.push(params.filters)
  return parts.join('&')
}

export function useTestfunctionSets(params: UseTestfunctionSetsParams = {}) {
  return useQuery({
    queryKey: ['testfunction-sets', params],
    queryFn: async () => {
      const query = buildQuery(params)
      const { data } = await api.get<PaginatedResponse<TestfunctionSet> | TestfunctionSet[]>(
        `${endpoints.testfunctionSets}?${query}`,
      )
      if ('results' in data) return data
      return { count: data.length, next: null, previous: null, results: data }
    },
  })
}

export function useTestfunctionSet(name: string) {
  return useQuery({
    queryKey: ['testfunction-set', name],
    queryFn: async () => {
      const { data } = await api.get<TestfunctionSet>(
        endpoints.testfunctionSetDownload(name),
      )
      return data
    },
    enabled: !!name,
  })
}
