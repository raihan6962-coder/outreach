"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { DataTable, Column } from "@/components/layout/data-table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Separator } from "@/components/ui/separator"
import { toast } from "@/components/ui/toast"
import { Check, X, Reply, ThumbsUp, ThumbsDown, Calendar, MoveRight } from "lucide-react"
import { formatDateTime } from "@/lib/utils"

const replyTypeColors: Record<string, string> = {
  reply: "bg-blue-500",
  autoreply: "bg-yellow-500",
  bounce: "bg-red-500",
  ooo: "bg-purple-500",
  interested: "bg-green-500",
  not_interested: "bg-gray-500",
}

export default function RepliesPage() {
  const [replies, setReplies] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [typeFilter, setTypeFilter] = useState("all")
  const [sentimentFilter, setSentimentFilter] = useState("all")
  const [detailOpen, setDetailOpen] = useState(false)
  const [selectedReply, setSelectedReply] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [pipelineStages, setPipelineStages] = useState<any[]>([])
  const [selectedStage, setSelectedStage] = useState("")

  useEffect(() => {
    fetchReplies()
  }, [typeFilter, sentimentFilter])

  async function fetchReplies() {
    try {
      setLoading(true)
      const params: Record<string, string> = { is_reply: "true" }
      if (typeFilter !== "all") params.intent = typeFilter
      if (sentimentFilter !== "all") params.sentiment = sentimentFilter
      const data = await api.getInbox(params)
      setReplies(data)
    } catch {
      toast.error("Failed to load replies")
    } finally {
      setLoading(false)
    }
  }

  async function openDetail(reply: any) {
    setSelectedReply(reply)
    setDetailOpen(true)
    setDetailLoading(true)
    setSelectedStage("")
    try {
      const [stages] = await Promise.all([
        api.getPipelineStages(),
      ])
      setPipelineStages(stages)
    } catch {
      toast.error("Failed to load details")
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleClassify(interested: boolean) {
    if (!selectedReply) return
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/inbox/${selectedReply.id}/interested`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ interested }),
      })
      toast.success(interested ? "Marked as interested" : "Marked as not interested")
      fetchReplies()
    } catch {
      toast.error("Failed to classify")
    }
  }

  async function handleMoveStage() {
    if (!selectedReply || !selectedStage) return
    try {
      await api.moveLeadStage(selectedReply.id, selectedStage)
      toast.success("Moved to stage")
      setDetailOpen(false)
    } catch {
      toast.error("Failed to move stage")
    }
  }

  const columns: Column<any>[] = [
    { header: "From", accessor: "from_email", sortable: true },
    { header: "Subject", accessor: "subject", sortable: true },
    {
      header: "Reply Type",
      accessor: "intent",
      sortable: true,
      cell: (item) => (
        <Badge className={`${replyTypeColors[item.intent] || "bg-gray-500"} text-white text-xs`}>
          <Reply className="h-3 w-3 mr-1" />
          {item.intent || "unknown"}
        </Badge>
      ),
    },
    {
      header: "Is Positive",
      accessor: "sentiment",
      cell: (item) =>
        item.sentiment === "positive" ? (
          <Check className="h-4 w-4 text-green-500" />
        ) : item.sentiment === "negative" ? (
          <X className="h-4 w-4 text-red-500" />
        ) : (
          <span className="text-muted-foreground text-sm">-</span>
        ),
    },
    {
      header: "Received Date",
      accessor: "received_at",
      sortable: true,
      cell: (item) => formatDateTime(item.received_at || item.created_at),
    },
    {
      header: "Actions",
      accessor: "id",
      cell: (item) => (
        <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); openDetail(item) }}>
          View
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Replies" description="Manage email replies from your campaigns" />

      <div className="flex gap-3 flex-wrap">
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Reply Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="reply">Reply</SelectItem>
            <SelectItem value="autoreply">Auto Reply</SelectItem>
            <SelectItem value="bounce">Bounce</SelectItem>
            <SelectItem value="ooo">Out of Office</SelectItem>
            <SelectItem value="interested">Interested</SelectItem>
            <SelectItem value="not_interested">Not Interested</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sentimentFilter} onValueChange={setSentimentFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Sentiment" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sentiment</SelectItem>
            <SelectItem value="positive">Positive</SelectItem>
            <SelectItem value="negative">Negative</SelectItem>
            <SelectItem value="neutral">Neutral</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={replies}
        keyField="id"
        isLoading={loading}
        searchable
        searchPlaceholder="Search replies..."
        pageSize={15}
        emptyMessage="No replies found."
        onRowClick={openDetail}
      />

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Reply Details</DialogTitle>
            <DialogDescription>Review the reply and take action</DialogDescription>
          </DialogHeader>
          {detailLoading ? (
            <div className="space-y-3 py-4">
              <div className="h-5 w-48 bg-muted animate-pulse rounded" />
              <div className="h-4 w-32 bg-muted animate-pulse rounded" />
              <Separator />
              <div className="h-24 w-full bg-muted animate-pulse rounded" />
            </div>
          ) : selectedReply ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-lg">{selectedReply.subject}</h3>
                <div className="text-sm text-muted-foreground space-y-1 mt-2">
                  <p><span className="font-medium text-foreground">From:</span> {selectedReply.from_email}</p>
                  <p><span className="font-medium text-foreground">To:</span> {selectedReply.to_email}</p>
                  <p><span className="font-medium text-foreground">Date:</span> {formatDateTime(selectedReply.received_at || selectedReply.created_at)}</p>
                </div>
              </div>
              {selectedReply.intent && (
                <div>
                  <Badge className={`${replyTypeColors[selectedReply.intent] || "bg-gray-500"} text-white`}>
                    {selectedReply.intent}
                  </Badge>
                </div>
              )}
              <Separator />
              <div className="text-sm whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                {selectedReply.body}
              </div>
              <Separator />
              <div>
                <p className="text-sm font-medium mb-2">Classification</p>
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => handleClassify(true)}>
                    <ThumbsUp className="h-4 w-4 mr-1" /> Interested
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleClassify(false)}>
                    <ThumbsDown className="h-4 w-4 mr-1" /> Not Interested
                  </Button>
                  <Button size="sm" variant="secondary">
                    <Calendar className="h-4 w-4 mr-1" /> Meeting
                  </Button>
                </div>
              </div>
              <div>
                <p className="text-sm font-medium mb-2">Move to Pipeline Stage</p>
                <div className="flex gap-2">
                  <Select value={selectedStage} onValueChange={setSelectedStage}>
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select stage" />
                    </SelectTrigger>
                    <SelectContent>
                      {pipelineStages.map((stage: any) => (
                        <SelectItem key={stage.id} value={stage.id}>{stage.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button size="sm" onClick={handleMoveStage} disabled={!selectedStage}>
                    <MoveRight className="h-4 w-4 mr-1" /> Move
                  </Button>
                </div>
              </div>
            </div>
          ) : null}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDetailOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
