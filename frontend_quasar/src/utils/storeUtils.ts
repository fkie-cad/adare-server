import { api } from 'src/boot/axios';

export async function fetchItems(endpoint: string, query: string) {
  const data = await api.get(`${endpoint}/?${query}`).then(res => res.data);
  // if key 'results' is present, we are dealing with a paginated response
  if ('results' in data) {
    return data.results;
  } else {
    return data;
  }
}

export interface ScopedFilterParams {
  tags_scoped?: string[];
  environment_mc?: string[];
  os_mc?: string[];
  testfunction_set?: string;
}

export function buildFilterQuery(params: ScopedFilterParams): string {
  const parts: string[] = [];
  if (params.tags_scoped && params.tags_scoped.length > 0) {
    parts.push(`tags_scoped=${params.tags_scoped.join(',')}`);
  }
  if (params.environment_mc && params.environment_mc.length > 0) {
    parts.push(`environment_mc=${params.environment_mc.join(',')}`);
  }
  if (params.os_mc && params.os_mc.length > 0) {
    parts.push(`os_mc=${params.os_mc.join(',')}`);
  }
  if (params.testfunction_set) {
    parts.push(`testfunction_set=${params.testfunction_set}`);
  }
  return parts.join('&');
}

export async function fetchAdvancedItems(
  endpoint: string,
  fetchFunction: (query: string) => Promise<void>,
  limit?: number,
  offset?: number,
  sortBy?: string,
  descending?: boolean,
  filterString?: string,
  scopedFilters?: ScopedFilterParams,
) {
  let query = '';
  if (limit !== undefined || offset !== undefined || sortBy || filterString || scopedFilters) {
    query += '?';
  }
  if (limit !== undefined) {
    query += `limit=${limit}`;
  }
  if (offset !== undefined) {
    query += `&offset=${offset}`;
  }

  if (sortBy) {
    query += `&ordering=${descending ? '-' : ''}${sortBy}`;
  }
  if (filterString) {
    query += `&search=${filterString}`;
  }
  if (scopedFilters) {
    const scopedQuery = buildFilterQuery(scopedFilters);
    if (scopedQuery) {
      query += `&${scopedQuery}`;
    }
  }

  await fetchFunction(query);
}

export async function fetchFilterOptions(endpoint: string, query: string) {
  return await api.get(`${endpoint}/filteroptions/${query}`).then(res => res.data);
}
