import { useState } from 'react'
import type { ColumnDef, PaginationState, SortingState } from '@tanstack/react-table'
import { useRequests } from '@/api/hooks/use-requests'
import { DataTable } from '@/components/data-table/data-table'
import { PageContainer } from '@/components/layout/page-container'
import { StatusIcon } from '@/components/shared/status-icon'
import type { Request } from '@/types/experiment'

const columns: ColumnDef<Request, unknown>[] = [
  {
    accessorKey: 'gitea_pr_status',
    header: '',
    cell: ({ getValue }) => <StatusIcon status={getValue() as string} />,
    enableSorting: false,
  },
  {
    accessorKey: 'object',
    header: 'Object',
    cell: ({ getValue }) => {
      const obj = getValue() as Request['object']
      return (obj?.name as string) ?? ''
    },
  },
  { accessorKey: 'objective_name', header: 'Objective' },
  { accessorKey: 'action', header: 'Action' },
  {
    accessorKey: 'requester',
    header: 'Requester',
    cell: ({ getValue }) => (getValue() as Request['requester'])?.username ?? '',
  },
  { accessorKey: 'creation_date', header: 'Created', meta: { mono: true } },
  { accessorKey: 'last_change_date', header: 'Last changed', meta: { mono: true } },
]

export default function RequestListPage() {
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 8 })
  const [sorting, setSorting] = useState<SortingState>([])
  const [search, setSearch] = useState('')

  const { data, isLoading } = useRequests({
    limit: pagination.pageSize,
    offset: pagination.pageIndex * pagination.pageSize,
    sortBy: sorting[0]?.id,
    descending: sorting[0]?.desc,
    search: search || undefined,
  })

  return (
    <PageContainer>
    <DataTable
      title="Requests"
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
    </PageContainer>
  )
}
