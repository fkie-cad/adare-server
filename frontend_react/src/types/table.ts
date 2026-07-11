import type { RowData } from '@tanstack/react-table'

declare module '@tanstack/react-table' {
  // Column-level opt-in: renders machine data (ids, numbers, timestamps) as a
  // tabular-figure mono readout instead of body text.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData extends RowData, TValue> {
    mono?: boolean
  }
}

export interface FilterEntry {
  field: string
  type: string
  value: string
}

export interface Filter {
  entries: FilterEntry[]
}

export interface SelectFilter {
  name: string
  field: string
  api_field: string
  option_api_field: string
  type: string
  options: string[]
  total_options: string[]
  selected: string[]
}

export function filterToQueryString(filter: Filter): string {
  return filter.entries.map((entry) => `${entry.field}=${entry.value}`).join('&')
}
