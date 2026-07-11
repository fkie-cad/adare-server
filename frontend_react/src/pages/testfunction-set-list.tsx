import { useState } from 'react'
import type { ColumnDef, PaginationState, SortingState } from '@tanstack/react-table'
import { useTestfunctionSets } from '@/api/hooks/use-testfunction-sets'
import { DataTable } from '@/components/data-table/data-table'
import { PageContainer } from '@/components/layout/page-container'
import { DetailsCell } from '@/components/data-table/columns/details-cell'
import { UserIconCell } from '@/components/data-table/columns/user-icon-cell'
import { LinkCell } from '@/components/data-table/columns/link-cell'
import type { TestfunctionSet } from '@/types/experiment'

const columns: ColumnDef<TestfunctionSet, unknown>[] = [
  {
    id: 'details',
    header: '',
    cell: ({ row }) => <DetailsCell to={`/testfunctionset/${row.original.name}`} />,
    enableSorting: false,
  },
  { accessorKey: 'name', header: 'Name', enableSorting: true },
  { accessorKey: 'description', header: 'Description' },
  { accessorKey: 'num_testfunctions', header: '# Functions', meta: { mono: true } },
  {
    accessorKey: 'published_by',
    header: 'Published by',
    cell: ({ getValue }) => <UserIconCell username={getValue() as string} />,
  },
  { accessorKey: 'published_at', header: 'Publish date', meta: { mono: true } },
  {
    accessorKey: 'file',
    header: 'File',
    cell: ({ getValue }) => <LinkCell url={getValue() as string} tooltip="Open in Gitea" />,
  },
  {
    accessorKey: 'requirements_file',
    header: 'Requirements',
    cell: ({ getValue }) => <LinkCell url={getValue() as string} tooltip="Open in Gitea" />,
  },
]

export default function TestfunctionSetListPage() {
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 8 })
  const [sorting, setSorting] = useState<SortingState>([])
  const [search, setSearch] = useState('')

  const { data, isLoading } = useTestfunctionSets({
    limit: pagination.pageSize,
    offset: pagination.pageIndex * pagination.pageSize,
    sortBy: sorting[0]?.id,
    descending: sorting[0]?.desc,
    search: search || undefined,
  })

  return (
    <PageContainer>
    <DataTable
      title="Testfunction Sets"
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
