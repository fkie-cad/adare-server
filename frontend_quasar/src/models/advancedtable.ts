export interface hideableColumnEntry {
  label: string;
  field: string;
}


export interface ColumnEntry {
  label: string;
  field: string;
  name: string;
  non_api_field?: boolean;
  default?: string;
  hideable?: boolean;
  disbale_filter?: boolean;
}


export interface FilterEntry {
  field: string;
  type: string;
  value: string;
}

export interface Filter {
  entries: FilterEntry[];
}

export interface ColumnFilter {
  [key: string]: string
}

export interface SelectFilter {
  name: string;
  field: string;
  api_field: string;
  option_api_field: string;
  type: string;
  options: string[];
  total_options: string[];
  selected: string[];
}

export function FilterToQueryString(filter: Filter): string {
  let query = '';
  filter.entries.forEach((entry) => {
      query += `&${entry.field}=${entry.value}`;
  });
  return query;
}
