"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { toast } from "@/components/ui/toast"
import { cn } from "@/lib/utils"
import { formatDateTime } from "@/lib/utils"
import { Plus, Mail, Power, Trash2, ExternalLink, Activity, Shield, RefreshCw, Eye, MessageSquare, Thermometer } from "lucide-react"

function HealthGauge({ value }: { value: number }) {
  const radius = 50
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(value / 100, 1)
  const offset = circumference * (1 - progress)
  const color = value >= 70 ? "#22c55e" : value >= 40 ? "#f59e0b" : "#ef4444"

  return (
    <svg width="120" height="120" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={radius} fill="none" stroke="hsl(var(--secondary))" strokeWidth="8" />
      <circle
        cx="60" cy="60" r={radius}
        fill="none" stroke={color}
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform="rotate(-90 60 60)"
        className="transition-all duration-700"
      />
      <text x="60" y="62" textAnchor="middle" dominantBaseline="central" className="text-xl font-bold" fill="currentColor">{Math.round(value)}</text>
      <text x="60" y="80" textAnchor="middle" dominantBaseline="central" className="text-[9px] fill-muted-foreground">Health</text>
    </svg>
  )
}

export default function GmailAccountsPage() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailData, setDetailData] = useState<any>(null)
  const [disconnectConfirm, setDisconnectConfirm] = useState<string | null>(null)
  const [toggling, setToggling] = useState<Record<string, boolean>>({})

  useEffect(() => {
    fetchAccounts()
  }, [])

  async function fetchAccounts() {
    try {
      setLoading(true)
      const data = await api.getGmailAccounts()
      setAccounts(data)
    } catch {
      toast.error("Failed to load Gmail accounts")
    } finally {
      setLoading(false)
    }
  }

  async function handleConnect() {
    try {
      setConnecting(true)
      const { auth_url } = await api.getGmailAuthUrl()
      const popup = window.open(auth_url, "gmail-auth", "width=600,height=700")
      if (!popup) {
        toast.error("Popup blocked. Please allow popups for this site.")
        return
      }
      const pollTimer = setInterval(() => {
        try {
          if (popup.closed) {
            clearInterval(pollTimer)
            fetchAccounts()
            setConnecting(false)
          }
          if (popup.location.href?.includes("callback") || popup.location.href?.includes("success")) {
            popup.close()
            clearInterval(pollTimer)
            fetchAccounts()
            setConnecting(false)
          }
        } catch {
          // cross-origin, continue polling
        }
      }, 1000)
    } catch {
      toast.error("Failed to start Gmail connection")
      setConnecting(false)
    }
  }

  async function handleToggle(account: any) {
    const id = account.id
    setToggling((prev) => ({ ...prev, [id]: true }))
    try {
      await api.toggleGmail(id, !account.is_active)
      toast.success(`${account.email} ${account.is_active ? "disabled" : "enabled"}`)
      fetchAccounts()
    } catch {
      toast.error("Failed to toggle account")
    } finally {
      setToggling((prev) => ({ ...prev, [id]: false }))
    }
  }

  async function handleDisconnect(id: string) {
    try {
      await api.disconnectGmail(id)
      toast.success("Account disconnected")
      setDisconnectConfirm(null)
      fetchAccounts()
    } catch {
      toast.error("Failed to disconnect account")
    }
  }

  async function openDetail(account: any) {
    setSelectedAccount(account)
    setDetailOpen(true)
    setDetailLoading(true)
    try {
      const health = await api.getGmailHealth(account.id)
      setDetailData(health)
    } catch {
      toast.error("Failed to load account details")
    } finally {
      setDetailLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Gmail Accounts"
        description="Manage your Gmail account connections"
        actions={
          <Button onClick={handleConnect} disabled={connecting}>
            <Plus className="h-4 w-4 mr-2" />
            {connecting ? "Connecting..." : "Connect Gmail"}
          </Button>
        }
      />

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-24 w-24 rounded-full mx-auto" />
                <Skeleton className="h-2 w-full" />
                <Skeleton className="h-2 w-3/4" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : accounts.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Mail className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-1">No accounts connected</h3>
            <p className="text-sm text-muted-foreground mb-4">Connect your first Gmail account to start sending emails.</p>
            <Button onClick={handleConnect} disabled={connecting}>
              <Plus className="h-4 w-4 mr-2" /> Connect Gmail
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => {
            const usagePercent = account.daily_send_limit > 0
              ? Math.min((account.daily_send_count / account.daily_send_limit) * 100, 100)
              : 0

            return (
              <Card key={account.id} className="group">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-base truncate">{account.email}</CardTitle>
                      <CardDescription className="text-xs">{account.display_name || ""}</CardDescription>
                    </div>
                    <div className={`h-3 w-3 rounded-full shrink-0 mt-1 ${account.is_active ? "bg-green-500" : "bg-red-500"}`} />
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-center">
                    <HealthGauge value={account.health_score ?? 75} />
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Daily Usage</span>
                      <span>{account.daily_send_count}/{account.daily_send_limit}</span>
                    </div>
                    <Progress value={usagePercent} className="h-2" />
                  </div>
                  <div className="flex flex-wrap gap-1">
                    <Badge variant="outline" className="text-xs flex items-center gap-1">
                      <Eye className="h-3 w-3" /> {account.inbox_rate ? `${(account.inbox_rate * 100).toFixed(0)}%` : "-"} Inbox
                    </Badge>
                    <Badge variant="outline" className="text-xs flex items-center gap-1">
                      <Activity className="h-3 w-3" /> {account.spam_rate ? `${(account.spam_rate * 100).toFixed(0)}%` : "-"} Spam
                    </Badge>
                    <Badge variant="outline" className="text-xs flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" /> {account.reply_rate ? `${(account.reply_rate * 100).toFixed(0)}%` : "-"} Reply
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <Badge className={cn(
                      "text-xs",
                      account.warmup_status === "warmed" ? "bg-green-500 text-white" :
                      account.warmup_status === "warming" ? "bg-yellow-500 text-white" : ""
                    )} variant={account.warmup_status === "none" ? "secondary" : "default"}>
                      <Thermometer className="h-3 w-3 mr-1" />
                      {account.warmup_status || "none"}
                    </Badge>
                    <span>Last sent: {account.last_send_reset ? formatDateTime(account.last_send_reset) : "Never"}</span>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t">
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={account.is_active}
                        onCheckedChange={() => handleToggle(account)}
                        disabled={toggling[account.id]}
                      />
                      <span className="text-xs text-muted-foreground">{account.is_active ? "Enabled" : "Disabled"}</span>
                    </div>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openDetail(account)}>
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive"
                        onClick={() => setDisconnectConfirm(account.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Account Details</DialogTitle>
            <DialogDescription>{selectedAccount?.email}</DialogDescription>
          </DialogHeader>
          {detailLoading ? (
            <div className="space-y-4 py-4">
              <Skeleton className="h-20 w-20 rounded-full mx-auto" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : detailData ? (
            <div className="space-y-4">
              <div className="flex justify-center">
                <HealthGauge value={detailData.health_score ?? 0} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1 text-sm">
                  <p className="text-muted-foreground">Total Sent</p>
                  <p className="font-semibold text-lg">{detailData.total_sent ?? 0}</p>
                </div>
                <div className="space-y-1 text-sm">
                  <p className="text-muted-foreground">Total Opens</p>
                  <p className="font-semibold text-lg">{detailData.total_opens ?? 0}</p>
                </div>
                <div className="space-y-1 text-sm">
                  <p className="text-muted-foreground">Total Replies</p>
                  <p className="font-semibold text-lg">{detailData.total_replies ?? 0}</p>
                </div>
                <div className="space-y-1 text-sm">
                  <p className="text-muted-foreground">Total Bounces</p>
                  <p className="font-semibold text-lg">{detailData.total_bounces ?? 0}</p>
                </div>
              </div>
              <Separator />
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Inbox Rate</span>
                  <span className="font-medium">{detailData.inbox_rate ? `${(detailData.inbox_rate * 100).toFixed(1)}%` : "-"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Spam Rate</span>
                  <span className="font-medium">{detailData.spam_rate ? `${(detailData.spam_rate * 100).toFixed(1)}%` : "-"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Reply Rate</span>
                  <span className="font-medium">{detailData.reply_rate ? `${(detailData.reply_rate * 100).toFixed(1)}%` : "-"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Open Rate</span>
                  <span className="font-medium">{detailData.open_rate ? `${(detailData.open_rate * 100).toFixed(1)}%` : "-"}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground text-sm">No detail data available</div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDetailOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!disconnectConfirm} onOpenChange={(open) => !open && setDisconnectConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Disconnect Account</DialogTitle>
            <DialogDescription>
              Are you sure you want to disconnect this Gmail account? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDisconnectConfirm(null)}>Cancel</Button>
            <Button variant="destructive" onClick={() => disconnectConfirm && handleDisconnect(disconnectConfirm)}>
              <Trash2 className="h-4 w-4 mr-2" /> Disconnect
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
