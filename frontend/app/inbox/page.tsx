"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Search, Mail, MailOpen, Reply, ArrowLeft, ThumbsUp, ThumbsDown } from "lucide-react"
import { formatDateTime } from "@/lib/utils"

export default function InboxPage() {
  const [messages, setMessages] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filterTab, setFilterTab] = useState("all")
  const [search, setSearch] = useState("")
  const [detailLoading, setDetailLoading] = useState(false)
  const [detail, setDetail] = useState<any>(null)

  const fetchMessages = async () => {
    try {
      setLoading(true)
      const params: Record<string, string> = {}
      if (filterTab === "unread") params.is_read = "false"
      if (filterTab === "replied") params.is_reply = "true"
      if (search) params.search = search
      const data = await api.getInbox(params)
      setMessages(data)
    } catch (err) {
      console.error("Failed to fetch inbox", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMessages()
  }, [filterTab])

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchMessages()
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      return
    }
    async function loadDetail() {
      try {
        setDetailLoading(true)
        const data = await api.getInboxMessage(selectedId)
        setDetail(data)
      } catch (err) {
        console.error("Failed to load message detail", err)
      } finally {
        setDetailLoading(false)
      }
    }
    loadDetail()
  }, [selectedId])

  const handleMarkInterested = async () => {
    if (!detail) return
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/inbox/${detail.id}/interested`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ interested: true }),
      })
    } catch (err) {
      console.error("Failed to mark interested", err)
    }
  }

  const handleMarkNotInterested = async () => {
    if (!detail) return
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/inbox/${detail.id}/interested`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ interested: false }),
      })
    } catch (err) {
      console.error("Failed to mark not interested", err)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Inbox" />

      <div className="flex gap-4 h-[calc(100vh-12rem)]">
        <div className={`w-full md:w-96 shrink-0 flex flex-col gap-3 ${selectedId ? "hidden md:flex" : "flex"}`}>
          <div className="flex items-center gap-2">
            <Tabs value={filterTab} onValueChange={setFilterTab}>
              <TabsList>
                <TabsTrigger value="all">All</TabsTrigger>
                <TabsTrigger value="unread">Unread</TabsTrigger>
                <TabsTrigger value="replied">Replied</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search inbox..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>
          <div className="flex-1 overflow-y-auto space-y-1">
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="p-3 space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                ))}
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Mail className="h-12 w-12 text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">Inbox is empty</p>
              </div>
            ) : (
              messages.map((msg) => (
                <button
                  key={msg.id}
                  className={`w-full text-left p-3 rounded-lg transition-colors hover:bg-accent ${
                    selectedId === msg.id ? "bg-accent" : ""
                  } ${!msg.is_read ? "font-semibold bg-accent/50" : ""}`}
                  onClick={() => setSelectedId(msg.id)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm truncate flex-1">{msg.from_email}</span>
                    <div className="flex items-center gap-1">
                      {!msg.is_read && <span className="h-2 w-2 rounded-full bg-primary shrink-0" />}
                      {msg.is_reply && <Reply className="h-3 w-3 text-muted-foreground shrink-0" />}
                      <span className="text-xs text-muted-foreground shrink-0">{formatDateTime(msg.received_at || msg.created_at)}</span>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground truncate">{msg.subject}</p>
                </button>
              ))
            )}
          </div>
        </div>

        <div className={`flex-1 ${!selectedId ? "hidden md:block" : "block"}`}>
          {selectedId && (
            <Button variant="ghost" size="sm" className="mb-2 md:hidden" onClick={() => setSelectedId(null)}>
              <ArrowLeft className="h-4 w-4 mr-1" /> Back
            </Button>
          )}
          {detailLoading ? (
            <Card>
              <CardContent className="p-6 space-y-4">
                <Skeleton className="h-6 w-64" />
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-32" />
                <Separator />
                <Skeleton className="h-32 w-full" />
              </CardContent>
            </Card>
          ) : detail ? (
            <Card>
              <CardContent className="p-6 space-y-4">
                <div>
                  <h2 className="text-xl font-semibold mb-2">{detail.subject}</h2>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <p><span className="font-medium text-foreground">From:</span> {detail.from_email}</p>
                    <p><span className="font-medium text-foreground">To:</span> {detail.to_email}</p>
                    <p><span className="font-medium text-foreground">Date:</span> {formatDateTime(detail.received_at || detail.created_at)}</p>
                  </div>
                </div>
                {detail.intent && (
                  <div>
                    <Badge variant="outline" className="text-xs">
                      <Reply className="h-3 w-3 mr-1" /> Reply: {detail.intent}
                    </Badge>
                  </div>
                )}
                <Separator />
                <div className="text-sm whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
                  {detail.body}
                </div>
                <Separator />
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleMarkInterested}>
                    <ThumbsUp className="h-4 w-4 mr-1" /> Mark Interested
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleMarkNotInterested}>
                    <ThumbsDown className="h-4 w-4 mr-1" /> Not Interested
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center">
                <MailOpen className="h-16 w-16 mx-auto mb-3 opacity-30" />
                <p>Select a message to read</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
