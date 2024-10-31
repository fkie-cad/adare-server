import { api } from 'src/boot/axios';

export async function fetchItems(endpoint: string, query: string) {
  const data = await api.get(`${endpoint}/${query}`).then(res => res.data);
  // if key 'results' is present, we are dealing with a paginated response
  if ('results' in data) {
    return data.results;
  } else {
    return data;
  }
}

export async function fetchAdvancedItems(
  endpoint: string,
  fetchFunction: (query: string) => Promise<void>,
  limit?: number,
  offset?: number,
  sortBy?: string,
  descending?: boolean,
  filterString?: string
) {
  let query = '';
  if (limit !== undefined || offset !== undefined || sortBy || filterString) {
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

  await fetchFunction(query);
}

export async function fetchFilterOptions(endpoint: string, query: string) {
  return await api.get(`${endpoint}/filteroptions/${query}`).then(res => res.data);
}
