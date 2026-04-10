import { useState } from 'react'
import type { Table } from '@tanstack/react-table'
import { Settings, Search, Filter } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface DataTablePanelProps<TData> {
  title: string
  table: Table<TData>
  searchValue?: string
  onSearchChange?: (value: string) => void
  onFilterToggle?: () => void
  filterActive?: boolean
}

export function DataTablePanel<TData>({
  title,
  table,
  searchValue = '',
  onSearchChange,
  onFilterToggle,
  filterActive,
}: DataTablePanelProps<TData>) {
  const [showColumnMenu, setShowColumnMenu] = useState(false)

  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">{title}</h2>
        {onFilterToggle && (
          <Button
            variant={filterActive ? 'default' : 'outline'}
            size="sm"
            onClick={onFilterToggle}
            className="gap-1"
          >
            <Filter className="h-3.5 w-3.5" />
            Filters
          </Button>
        )}
      </div>

      <div className="flex items-center gap-2 ml-auto">
        {onSearchChange && (
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-8 w-64"
            />
          </div>
        )}

        <div className="relative">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowColumnMenu(!showColumnMenu)}
          >
            <Settings className="h-4 w-4" />
          </Button>
          {showColumnMenu && (
            <div className="absolute right-0 top-full mt-1 bg-popover text-popover-foreground rounded-md shadow-lg border border-border p-2 min-w-48 z-50">
              <div className="flex gap-2 mb-2 px-2">
                <button
                  className="text-xs text-secondary hover:underline"
                  onClick={() => table.toggleAllColumnsVisible(true)}
                >
                  Show all
                </button>
                <button
                  className="text-xs text-secondary hover:underline"
                  onClick={() => table.toggleAllColumnsVisible(false)}
                >
                  Hide all
                </button>
              </div>
              {table.getAllLeafColumns().map((column) => (
                <label
                  key={column.id}
                  className="flex items-center gap-2 px-2 py-1 text-sm hover:bg-accent rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={column.getIsVisible()}
                    onChange={column.getToggleVisibilityHandler()}
                    className="rounded"
                  />
                  {typeof column.columnDef.header === 'string'
                    ? column.columnDef.header
                    : column.id}
                </label>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
