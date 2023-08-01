interface hideableColumnEntry {
  label: string;
  field: string;
}


interface ColumnEntry {
  label: string;
  field: string;
  name: string;
  non_api_field?: boolean;
  default?: string;
  hideable?: boolean;
  disbale_filter?: boolean;
}


interface FilterEntry {
  field: string;
  type: string;
  value: string;
}

interface Filter {
  entries: FilterEntry[];
}

interface ColumnFilter {
  [key: string]: string
}

function FilterToQueryString(filter: Filter): string {
  let query = '';
  filter.entries.forEach((entry) => {
    query += `&${entry.field}=${entry.value}`
  })
  return query
}


export type { Filter, ColumnFilter, hideableColumnEntry, ColumnEntry };
export { FilterToQueryString };
