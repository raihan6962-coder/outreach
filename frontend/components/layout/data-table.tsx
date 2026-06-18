"use client"

import { useState, useMemo, useCallback } from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Skeleton } from "@/components/ui/skeleton"
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight, Search } from "lucide-react"
import { cn } from "@/lib/utils"

export interface Column<T> {
  header: string
  accessor: keyof T | ((item: T) => string | number | React.ReactNode)
  sortable?: boolean
  cell?: (item: T) => React.ReactNode
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyField: keyof T
  isLoading?: boolean
  searchable?: boolean
  searchPlaceholder?: string
  pageSize?: number
  emptyMessage?: string
  onRowClick?: (item: T) => void
  onSelectionChange?: (selected: T[]) => void
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  keyField,
  isLoading = false,
  searchable = false,
  searchPlaceholder = "Search...",
  pageSize = 10,
  emptyMessage = "No results found.",
  onRowClick,
  onSelectionChange,
}: DataTableProps<T>) {
  const [search, setSearch] = useState("")
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")
  const [page, setPage] = useState(0)
  const [selectedKeys, setSelectedKeys] = useState<Set<any>>(new Set())

  const filtered = useMemo(() => {
    if (!search.trim()) return data
    const q = search.toLowerCase()
    return data.filter((item) =>
      columns.some((col) => {
        if (typeof col.accessor === "function") return false
        const val = item[col.accessor]
        return val != null && String(val).toLowerCase().includes(q)
      })
    )
  }, [data, search, columns])

  const sorted = useMemo(() => {
    if (!sortColumn) return filtered
    return [...filtered].sort((a, b) => {
      const aVal = a[sortColumn]
      const bVal = b[sortColumn]
      if (aVal == null) return 1
      if (bVal == null) return -1
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0
      return sortDirection === "asc" ? cmp : -cmp
    })
  }, [filtered, sortColumn, sortDirection])

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const safePage = Math.min(page, totalPages - 1)
  const paginated = sorted.slice(safePage * pageSize, (safePage + 1) * pageSize)

  const allSelected = paginated.length > 0 && paginated.every((item) => selectedKeys.has(item[keyField]))
  const someSelected = paginated.some((item) => selectedKeys.has(item[keyField]))

  const handleSort = (col: string) => {
    if (sortColumn === col) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortColumn(col)
      setSortDirection("asc")
    }
  }

  const toggleAll = useCallback(() => {
    const next = new Set(selectedKeys)
    if (allSelected) {
      paginated.forEach((item) => next.delete(item[keyField]))
    } else {
      paginated.forEach((item) => next.add(item[keyField]))
    }
    setSelectedKeys(next)
    if (onSelectionChange) {
      onSelectionChange(data.filter((item) => next.has(item[keyField])))
    }
  }, [allSelected, paginated, selectedKeys, keyField, data, onSelectionChange])

  const toggleOne = useCallback(
    (key: any) => {
      const next = new Set(selectedKeys)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      setSelectedKeys(next)
      if (onSelectionChange) {
        onSelectionChange(data.filter((item) => next.has(item[keyField])))
      }
    },
    [selectedKeys, keyField, data, onSelectionChange]
  )

  const getValue = (item: T, col: Column<T>): React.ReactNode => {
    if (col.cell) return col.cell(item)
    if (typeof col.accessor === "function") return col.accessor(item) as React.ReactNode
    const val = item[col.accessor]
    return val != null ? String(val) : ""
  }

  const getSortKey = (col: Column<T>): string | null => {
    if (!col.sortable) return null
    return typeof col.accessor === "string" ? col.accessor : null
  }

  const renderSortIcon = (colKey: string | null) => {
    if (!colKey) return null
    if (sortColumn !== colKey) return <ChevronsUpDown className="ml-1 h-3 w-3" />
    return sortDirection === "asc" ? (
      <ChevronUp className="ml-1 h-3 w-3" />
    ) : (
      <ChevronDown className="ml-1 h-3 w-3" />
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {searchable && <Skeleton className="h-10 w-full max-w-sm" />}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {onSelectionChange && <TableHead className="w-10"><Skeleton className="h-4 w-4" /></TableHead>}
                {columns.map((col, i) => (
                  <TableHead key={i}><Skeleton className="h-4 w-24" /></TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {onSelectionChange && (
                    <TableCell><Skeleton className="h-4 w-4" /></TableCell>
                  )}
                  {columns.map((_, j) => (
                    <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {searchable && (
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(0)
            }}
            className="pl-8"
          />
        </div>
      )}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {onSelectionChange && (
                <TableHead className="w-10">
                  <Checkbox
                    checked={allSelected}
                    indeterminate={!allSelected && someSelected}
                    onCheckedChange={toggleAll}
                  />
                </TableHead>
              )}
              {columns.map((col, i) => {
                const sortKey = getSortKey(col)
                return (
                  <TableHead
                    key={i}
                    className={cn(sortKey && "cursor-pointer select-none")}
                    onClick={() => sortKey && handleSort(sortKey)}
                  >
                    <div className="flex items-center">
                      {col.header}
                      {renderSortIcon(sortKey)}
                    </div>
                  </TableHead>
                )
              })}
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginated.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length + (onSelectionChange ? 1 : 0)}
                  className="h-24 text-center text-muted-foreground"
                >
                  {emptyMessage}
                </TableCell>
              </TableRow>
            ) : (
              paginated.map((item) => (
                <TableRow
                  key={String(item[keyField])}
                  className={cn(onRowClick && "cursor-pointer")}
                  onClick={() => onRowClick?.(item)}
                >
                  {onSelectionChange && (
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedKeys.has(item[keyField])}
                        onCheckedChange={() => toggleOne(item[keyField])}
                      />
                    </TableCell>
                  )}
                  {columns.map((col, i) => (
                    <TableCell key={i}>{getValue(item, col)}</TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {safePage + 1} of {totalPages}
          </p>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              disabled={safePage === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              disabled={safePage >= totalPages - 1}
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
