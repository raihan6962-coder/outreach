"use client"

import { useState, useEffect, useCallback } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import { Search, Upload, Download, Trash2, Edit, ChevronLeft, ChevronRight, Users } from "lucide-react"
import { formatDate } from "@/lib/utils"

const validationColors: Record<string, string> = {
  pending: "bg-gray-500",
  valid: "bg-green-500",
  invalid: "bg-red-500",
  unknown: "bg-yellow-500",
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [validationFilter, setValidationFilter] = useState("all")
  const [sentFilter, setSentFilter] = useState("all")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [page, setPage] = useState(0)
  const [editOpen, setEditOpen] = useState(false)
  const [editingLead, setEditingLead] = useState<any>(null)
  const [editTags, setEditTags] = useState("")
  const [editNotes, setEditNotes] = useState("")
  const pageSize = 10

  const fetchLeads = useCallback(async () => {
    try {
      setLoading(true)
      const params: Record<string, string> = {}
      if (search) params.search = search
      if (validationFilter !== "all") params.validation_status = validationFilter
      if (sentFilter !== "all") params.sent_status = sentFilter
      if (categoryFilter) params.category = categoryFilter
      const data = await api.getLeads(params)
      setLeads(data)
    } catch (err) {
      console.error("Failed to fetch leads", err)
    } finally {
      setLoading(false)
    }
  }, [search, validationFilter, sentFilter, categoryFilter])

  useEffect(() => {
    fetchLeads()
  }, [fetchLeads])

  const paginatedLeads = leads.slice(page * pageSize, (page + 1) * pageSize)
  const totalPages = Math.max(1, Math.ceil(leads.length / pageSize))

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (paginatedLeads.every((l) => selected.has(l.id))) {
      setSelected(new Set())
    } else {
      setSelected(new Set(paginatedLeads.map((l) => l.id)))
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await api.deleteLead(id)
      setSelected((prev) => { const n = new Set(prev); n.delete(id); return n })
      fetchLeads()
    } catch (err) {
      console.error("Failed to delete lead", err)
    }
  }

  const handleBulkDelete = async () => {
    try {
      await api.deleteLeadsBulk(Array.from(selected))
      setSelected(new Set())
      fetchLeads()
    } catch (err) {
      console.error("Failed to bulk delete", err)
    }
  }

  const openEdit = (lead: any) => {
    setEditingLead(lead)
    setEditTags((lead.tags ?? []).join(", "))
    setEditNotes(lead.notes ?? "")
    setEditOpen(true)
  }

  const handleEditSave = async () => {
    if (!editingLead) return
    try {
      await api.updateLeadTags(editingLead.id, editTags.split(",").map((t: string) => t.trim()).filter(Boolean))
      if (editNotes !== (editingLead.notes ?? "")) {
        await api.addLeadNote(editingLead.id, editNotes)
      }
      setEditOpen(false)
      setEditingLead(null)
      fetchLeads()
    } catch (err) {
      console.error("Failed to update lead", err)
    }
  }

  const handleImportCsv = () => {
    const input = document.createElement("input")
    input.type = "file"
    input.accept = ".csv"
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0]
      if (!file) return
      const formData = new FormData()
      formData.append("file", file)
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/leads/import`, {
          method: "POST",
          headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
          body: formData,
        })
        fetchLeads()
      } catch (err) {
        console.error("Import failed", err)
      }
    }
    input.click()
  }

  const handleExportCsv = () => {
    const csv = ["email,first_name,last_name,company,position,tags,notes"]
    leads.forEach((l) => {
      csv.push(`${l.email || ""},${l.first_name || ""},${l.last_name || ""},${l.company || ""},${l.position || ""},"${(l.tags || []).join("; ")}","${(l.notes || "").replace(/"/g, '""')}"`)
    })
    const blob = new Blob([csv.join("\n")], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "leads.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leads"
        actions={
          <>
            <Button variant="outline" onClick={handleImportCsv}>
              <Upload className="h-4 w-4 mr-2" /> Import CSV
            </Button>
            <Button variant="outline" onClick={handleExportCsv}>
              <Download className="h-4 w-4 mr-2" /> Export CSV
            </Button>
          </>
        }
      />

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search leads..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0) }}
            className="pl-8"
          />
        </div>
        <Select value={validationFilter} onValueChange={(v) => { setValidationFilter(v); setPage(0) }}>
          <SelectTrigger className="w-[160px]"><SelectValue placeholder="Validation" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="valid">Valid</SelectItem>
            <SelectItem value="invalid">Invalid</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="unknown">Unknown</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sentFilter} onValueChange={(v) => { setSentFilter(v); setPage(0) }}>
          <SelectTrigger className="w-[160px]"><SelectValue placeholder="Sent Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="sent">Sent</SelectItem>
            <SelectItem value="not_sent">Not Sent</SelectItem>
          </SelectContent>
        </Select>
        <Input
          type="text"
          placeholder="Category"
          value={categoryFilter}
          onChange={(e) => { setCategoryFilter(e.target.value); setPage(0) }}
          className="w-[160px]"
        />
      </div>

      {selected.size > 0 && (
        <div className="flex items-center gap-2">
          <Button variant="destructive" size="sm" onClick={handleBulkDelete}>
            <Trash2 className="h-4 w-4 mr-1" /> Delete Selected ({selected.size})
          </Button>
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : leads.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Users className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-1">No leads found</h3>
            <p className="text-sm text-muted-foreground">Import a CSV or add leads from a sheet source.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={paginatedLeads.length > 0 && paginatedLeads.every((l) => selected.has(l.id))}
                    onCheckedChange={toggleAll}
                  />
                </TableHead>
                <TableHead>Email</TableHead>
                <TableHead>App Name</TableHead>
                <TableHead>Developer</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Validation</TableHead>
                <TableHead>Sent</TableHead>
                <TableHead>Score</TableHead>
                <TableHead className="w-[80px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedLeads.map((lead) => (
                <TableRow key={lead.id}>
                  <TableCell>
                    <Checkbox checked={selected.has(lead.id)} onCheckedChange={() => toggleSelect(lead.id)} />
                  </TableCell>
                  <TableCell className="font-medium">{lead.email}</TableCell>
                  <TableCell>{lead.metadata?.app_name || lead.company || "-"}</TableCell>
                  <TableCell>{lead.metadata?.developer || lead.position || "-"}</TableCell>
                  <TableCell>{lead.metadata?.category || "-"}</TableCell>
                  <TableCell>
                    <Badge className={`${validationColors[lead.validation_status] ?? "bg-gray-500"} text-white`}>
                      {lead.validation_status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={lead.sent_status === "sent" ? "default" : "secondary"}>
                      {lead.sent_status ?? "not_sent"}
                    </Badge>
                  </TableCell>
                  <TableCell>{lead.metadata?.score ?? "-"}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(lead)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDelete(lead.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">Page {page + 1} of {totalPages} ({leads.length} total)</p>
          <div className="flex items-center gap-1">
            <Button variant="outline" size="icon" className="h-8 w-8" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" disabled={page >= totalPages - 1} onClick={() => setPage((p) => p + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Lead</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={editingLead?.email ?? ""} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma separated)</Label>
              <Input id="tags" value={editTags} onChange={(e) => setEditTags(e.target.value)} placeholder="tag1, tag2, tag3" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <textarea
                id="notes"
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                placeholder="Add notes..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)}>Cancel</Button>
            <Button onClick={handleEditSave}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
