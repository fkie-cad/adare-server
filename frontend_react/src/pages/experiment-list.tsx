import { useState } from 'react'
import type { ColumnDef, PaginationState, SortingState } from '@tanstack/react-table'
import { LayoutList, BarChart3, Tags } from 'lucide-react'
import { useExperiments, useExperimentFilterOptions } from '@/api/hooks/use-experiments'
import { DataTable } from '@/components/data-table/data-table'
import { DetailsCell } from '@/components/data-table/columns/details-cell'
import { UserIconCell } from '@/components/data-table/columns/user-icon-cell'
import { TagsCell } from '@/components/data-table/columns/tags-cell'
import { RunCountsCell } from '@/components/data-table/columns/run-counts-cell'
import { LinkCell } from '@/components/data-table/columns/link-cell'
import { FilterSidebar } from '@/components/data-table/filter-sidebar'
import { ActiveFilters } from '@/components/data-table/active-filters'
import { Button } from '@/components/ui/button'
import { ExperimentDashboardView } from '@/components/experiment/experiment-dashboard-view'
import { ExperimentTagCloudView } from '@/components/experiment/experiment-tag-cloud-view'
import type { Experiment } from '@/types/experiment'

type ViewTab = 'table' | 'dashboard' | 'tagcloud'

const columns: ColumnDef<Experiment, unknown>[] = [
  {
    id: 'details',
    header: '',
    cell: ({ row }) => <DetailsCell to={`/experiment/${row.original.name}`} />,
    enableSorting: false,
  },
  { accessorKey: 'name', header: 'Name', enableSorting: true },
  { accessorKey: 'description', header: 'Description' },
  { accessorKey: 'ulid', header: 'ULID', meta: { mono: true } },
  {
    accessorKey: 'published_by',
    header: 'Published by',
    cell: ({ getValue }) => <UserIconCell username={getValue() as string} />,
  },
  { accessorKey: 'published_at', header: 'Publish date', meta: { mono: true } },
  {
    accessorKey: 'created_by',
    header: 'Created by',
    cell: ({ getValue }) => <UserIconCell username={getValue() as string} />,
  },
  {
    accessorKey: 'tags',
    header: 'Tags',
    cell: ({ getValue }) => <TagsCell tags={getValue() as Experiment['tags']} />,
  },
  {
    accessorKey: 'run_counts',
    header: 'Run counts',
    cell: ({ getValue }) => <RunCountsCell counts={getValue() as Experiment['run_counts']} />,
  },
  {
    accessorKey: 'action_file',
    header: 'Action file',
    cell: ({ getValue }) => <LinkCell url={getValue() as string} tooltip="Open in Gitea" />,
  },
  {
    accessorKey: 'testset_file',
    header: 'Testset file',
    cell: ({ getValue }) => <LinkCell url={getValue() as string} tooltip="Open in Gitea" />,
  },
  {
    accessorKey: 'metadata_file',
    header: 'Metadata file',
    cell: ({ getValue }) => <LinkCell url={getValue() as string} tooltip="Open in Gitea" />,
  },
]

const tabs: { key: ViewTab; label: string; icon: typeof LayoutList }[] = [
  { key: 'table', label: 'Table', icon: LayoutList },
  { key: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { key: 'tagcloud', label: 'Tags', icon: Tags },
]

export default function ExperimentListPage() {
  const [activeTab, setActiveTab] = useState<ViewTab>('table')
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 8 })
  const [sorting, setSorting] = useState<SortingState>([])
  const [search, setSearch] = useState('')
  const [filterOpen, setFilterOpen] = useState(false)
  const [selectedTags, setSelectedTags] = useState<string[]>([])

  const tagFilter = selectedTags.length > 0 ? `tags_scoped=${selectedTags.join(',')}` : undefined
  const filters = tagFilter

  const { data, isLoading } = useExperiments({
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

  function handleTagClick(tagName: string) {
    setSelectedTags((prev) =>
      prev.includes(tagName) ? prev.filter((t) => t !== tagName) : [...prev, tagName],
    )
  }

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)]">
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

        {/* Tab bar */}
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <Button
              key={tab.key}
              variant={activeTab === tab.key ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab(tab.key)}
              className="gap-1.5"
            >
              <tab.icon className="h-3.5 w-3.5" />
              {tab.label}
            </Button>
          ))}
        </div>

        {/* View content */}
        {activeTab === 'table' && (
          <DataTable
            title="Experiments"
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
        )}

        {activeTab === 'dashboard' && (
          <ExperimentDashboardView filters={filters} />
        )}

        {activeTab === 'tagcloud' && (
          <ExperimentTagCloudView
            tagsByScope={tagsByScope}
            selectedTags={selectedTags}
            onTagClick={handleTagClick}
          />
        )}
      </div>
    </div>
  )
}
