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
}


export type { hideableColumnEntry, ColumnEntry };
