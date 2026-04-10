import { useState } from 'react'
import type { ColumnDef, PaginationState, SortingState } from '@tanstack/react-table'
import { useRuns } from '@/api/hooks/use-runs'
import { DataTable } from '@/components/data-table/data-table'
import { DetailsCell } from '@/components/data-table/columns/details-cell'
import { StatusCell } from '@/components/data-table/columns/status-cell'
import type { Run } from '@/types/experiment'

const columns: ColumnDef<Run, unknown>[] = [
  {
    accessorKey: 'result_status',
    header: '',
    cell: ({ getValue }) => <StatusCell status={getValue() as Run['result_status']} />,
    enableSorting: false,
  },
  { accessorKey: 'experiment', header: 'Experiment' },
  { accessorKey: 'environment', header: 'Environment' },
  { accessorKey: 'ulid', header: 'ULID' },
  {
    id: 'details',
    header: 'Details',
    cell: ({ row }) => <DetailsCell to={`/run/${row.original.ulid}`} />,
    enableSorting: false,
  },
]

export default function RunListPage() {
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 8 })
  const [sorting, setSorting] = useState<SortingState>([])
  const [search, setSearch] = useState('')

  const { data, isLoading, isError } = useRuns({
    limit: pagination.pageSize,
    offset: pagination.pageIndex * pagination.pageSize,
    sortBy: sorting[0]?.id,
    descending: sorting[0]?.desc,
    search: search || undefined,
  })

  return (
    <div className="space-y-4">
      {isError && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load experiment runs. Please try again later.
        </div>
      )}
      <DataTable
        title="Experiment Runs"
        columns={columns}
        data={data?.results ?? []}
        totalCount={data?.count ?? 0}
        isLoading={isLoading}
        pagination={pagination}
        onPaginationChange={setPagination}
        sorting={sorting}
        onSortingChange={setSorting}
        searchValue={search}
        onSearchChange={setSearch}
      />
    </div>
  )
}
