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
  scope?: string;
  color?: string;
}

export function FilterToQueryString(filter: Filter): string {
  let query = '';
  const scopedTags: string[] = [];

  filter.entries.forEach((entry) => {
    if (entry.field.startsWith('tags_scoped_')) {
      // Collect scoped tag values for merging into single tags_scoped param
      if (entry.value) {
        scopedTags.push(...entry.value.split(','));
      }
    } else {
      query += `&${entry.field}=${entry.value}`;
    }
  });

  if (scopedTags.length > 0) {
    query += `&tags_scoped=${scopedTags.join(',')}`;
  }

  return query;
}
