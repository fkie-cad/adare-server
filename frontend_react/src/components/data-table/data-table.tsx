import { useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type PaginationState,
  type SortingState,
  type VisibilityState,
} from '@tanstack/react-table'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { DataTablePanel } from './data-table-panel'
import { DataTablePagination } from './data-table-pagination'
import { Loader2 } from 'lucide-react'

interface DataTableProps<TData> {
  title: string
  columns: ColumnDef<TData, unknown>[]
  data: TData[]
  totalCount: number
  isLoading?: boolean
  pagination: PaginationState
  onPaginationChange: (pagination: PaginationState) => void
  sorting?: SortingState
  onSortingChange?: (sorting: SortingState) => void
  searchValue?: string
  onSearchChange?: (value: string) => void
  initialColumnVisibility?: VisibilityState
  onFilterToggle?: () => void
  filterActive?: boolean
}

export function DataTable<TData>({
  title,
  columns,
  data,
  totalCount,
  isLoading = false,
  pagination,
  onPaginationChange,
  sorting = [],
  onSortingChange,
  searchValue = '',
  onSearchChange,
  initialColumnVisibility = {},
  onFilterToggle,
  filterActive,
}: DataTableProps<TData>) {
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>(initialColumnVisibility)

  const pageCount = Math.ceil(totalCount / pagination.pageSize)

  const table = useReactTable({
    data,
    columns,
    pageCount,
    state: {
      pagination,
      sorting,
      columnVisibility,
    },
    onPaginationChange: (updater) => {
      const next = typeof updater === 'function' ? updater(pagination) : updater
      onPaginationChange(next)
    },
    onSortingChange: (updater) => {
      if (onSortingChange) {
        const next = typeof updater === 'function' ? updater(sorting) : updater
        onSortingChange(next)
      }
    },
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
  })

  return (
    <div className="space-y-4">
      <DataTablePanel
        title={title}
        table={table}
        searchValue={searchValue}
        onSearchChange={onSearchChange}
        onFilterToggle={onFilterToggle}
        filterActive={filterActive}
      />
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className={header.column.getCanSort() ? 'cursor-pointer select-none' : ''}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                    {{
                      asc: ' \u2191',
                      desc: ' \u2193',
                    }[header.column.getIsSorted() as string] ?? null}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading...
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell
                      key={cell.id}
                      className={cell.column.columnDef.meta?.mono ? 'font-mono tabular-nums' : undefined}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <DataTablePagination table={table} totalCount={totalCount} />
    </div>
  )
}
