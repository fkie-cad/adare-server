import { useState } from 'react'
import type { ColumnDef, PaginationState, SortingState } from '@tanstack/react-table'
import { useEnvironments } from '@/api/hooks/use-environments'
import { useExperimentFilterOptions } from '@/api/hooks/use-experiments'
import { DataTable } from '@/components/data-table/data-table'
import { DetailsCell } from '@/components/data-table/columns/details-cell'
import { UserIconCell } from '@/components/data-table/columns/user-icon-cell'
import { TagsCell } from '@/components/data-table/columns/tags-cell'
import { OsInfoCell } from '@/components/data-table/columns/os-info-cell'
import { LinkCell } from '@/components/data-table/columns/link-cell'
import { FilterSidebar } from '@/components/data-table/filter-sidebar'
import { ActiveFilters } from '@/components/data-table/active-filters'
import type { Environment } from '@/types/experiment'

const columns: ColumnDef<Environment, unknown>[] = [
  {
    id: 'details',
    header: '',
    cell: ({ row }) => <DetailsCell to={`/environment/${row.original.name}`} />,
    enableSorting: false,
  },
  { accessorKey: 'name', header: 'Name', enableSorting: true },
  { accessorKey: 'description', header: 'Description' },
  { accessorKey: 'ulid', header: 'ULID' },
  {
    accessorKey: 'published_by',
    header: 'Published by',
    cell: ({ getValue }) => <UserIconCell username={getValue() as string} />,
  },
  { accessorKey: 'published_at', header: 'Publish date' },
  {
    accessorKey: 'created_by',
    header: 'Created by',
    cell: ({ getValue }) => <UserIconCell username={getValue() as string} />,
  },
  {
    accessorKey: 'tags',
    header: 'Tags',
    cell: ({ getValue }) => <TagsCell tags={getValue() as Environment['tags']} />,
  },
  {
    accessorKey: 'os_info',
    header: 'OS',
    cell: ({ getValue }) => <OsInfoCell osInfo={getValue() as Environment['os_info']} />,
  },
  {
    accessorKey: 'file',
    header: 'File',
    cell: ({ getValue }) => <LinkCell url={getValue() as string} tooltip="Open in Gitea" />,
  },
]

export default function EnvironmentListPage() {
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 8 })
  const [sorting, setSorting] = useState<SortingState>([])
  const [search, setSearch] = useState('')
  const [filterOpen, setFilterOpen] = useState(false)
  const [selectedTags, setSelectedTags] = useState<string[]>([])

  const tagFilter = selectedTags.length > 0 ? `tags_scoped=${selectedTags.join(',')}` : undefined
  const filters = tagFilter

  const { data, isLoading } = useEnvironments({
    limit: pagination.pageSize,
    offset: pagination.pageIndex * pagination.pageSize,
    sortBy: sorting[0]?.id,
    descending: sorting[0]?.desc,
    search: search || undefined,
    filters,
  })

  const { data: filterOpts } = useExperimentFilterOptions(filters)
  const tagsByScope = filterOpts?.tags_by_scope ?? {}

  function handleRemoveTag(tag: string) {
    setSelectedTags(selectedTags.filter((t) => t !== tag))
  }

  return (
    <div className="flex -mx-4 -mt-4 min-h-[calc(100vh-3.5rem)]">
      <FilterSidebar
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
        tagsByScope={tagsByScope}
        selectedTags={selectedTags}
        onSelectedTagsChange={setSelectedTags}
      />
      <div className="flex-1 space-y-2 p-4">
        <ActiveFilters
          selectedTags={selectedTags}
          onRemove={handleRemoveTag}
          onClear={() => setSelectedTags([])}
        />
        <DataTable
          title="Environments"
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
          onFilterToggle={() => setFilterOpen(!filterOpen)}
          filterActive={filterOpen || selectedTags.length > 0}
        />
      </div>
    </div>
  )
}
