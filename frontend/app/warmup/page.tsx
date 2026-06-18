"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Thermometer, Activity, Settings, Play, BarChart3, Mail } from "lucide-react"
import { formatDate, formatDateTime } from "@/lib/utils"
import { cn } from "@/lib/utils"

function WarmupGauge({ value }: { value: number }) {
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(value / 100, 1)
  const offset = circumference * (1 - progress)
  const color = value >= 70 ? "#22c55e" : value >= 40 ? "#f59e0b" : "#ef4444"

  return (
    <svg width="100" height="100" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r={radius} fill="none" stroke="hsl(var(--secondary))" strokeWidth="8" />
      <circle
        cx="50" cy="50" r={radius}
        fill="none" stroke={color}
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform="rotate(-90 50 50)"
        className="transition-all duration-700"
      />
      <text x="50" y="52" textAnchor="middle" dominantBaseline="central" className="text-lg font-bold" fill="currentColor">{Math.round(value)}</text>
      <text x="50" y="68" textAnchor="middle" dominantBaseline="central" className="text-[8px] fill-muted-foreground">Score</text>
    </svg>
  )
}

export default function WarmupPage() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [configOpen, setConfigOpen] = useState(false)
  const [configAccount, setConfigAccount] = useState<any>(null)
  const [targetDaily, setTargetDaily] = useState(50)
  const [configuring, setConfiguring] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    try {
      setLoading(true)
      const accts = await api.getGmailAccounts()
      const enriched = await Promise.all(
        accts.map(async (acc: any) => {
          try {
            const [status, progress] = await Promise.all([
              api.getWarmupStatus(acc.id),
              api.getWarmupProgress(acc.id),
            ])
            return { ...acc, warmup: status, progress: Array.isArray(progress) ? progress : [] }
          } catch {
            return { ...acc, warmup: null, progress: [] }
          }
        })
      )
      setAccounts(enriched)
    } catch {
      toast.error("Failed to load warmup data")
    } finally {
      setLoading(false)
    }
  }

  function openConfig(account: any) {
    setConfigAccount(account)
    setTargetDaily(account.warmup?.target_daily_sends || 50)
    setConfigOpen(true)
  }

  async function handleConfigure() {
    if (!configAccount) return
    try {
      setConfiguring(true)
      await api.configureWarmup({
        gmail_account_id: configAccount.id,
        target_daily_sends: targetDaily,
      })
      toast.success("Warmup configured")
      setConfigOpen(false)
      fetchData()
    } catch {
      toast.error("Failed to configure warmup")
    } finally {
      setConfiguring(false)
    }
  }

  const warmupBadge = (status: string) => {
    if (status === "warming") return <Badge className="bg-yellow-500 text-white">Warming</Badge>
    if (status === "warmed") return <Badge className="bg-green-500 text-white">Warmed</Badge>
    return <Badge variant="secondary">None</Badge>
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Email Warmup" description="Gradually increase sending volume to build reputation" />

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-40" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-24 w-24 rounded-full mx-auto" />
                <Skeleton className="h-2 w-full" />
                <Skeleton className="h-8 w-24 mx-auto" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : accounts.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Mail className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-1">No Gmail accounts</h3>
            <p className="text-sm text-muted-foreground mb-4">Connect Gmail accounts first to start warming up.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => {
            const healthScore = account.warmup?.health_score ?? 0
            const warmupProgress = account.warmup?.progress_percent ?? 0
            const dailySent = account.warmup?.daily_sent ?? 0
            const targetSends = account.warmup?.target_daily_sends ?? 50
            const dailyPercent = Math.min((dailySent / targetSends) * 100, 100)

            return (
              <Card key={account.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{account.email}</CardTitle>
                      <CardDescription className="text-xs">{account.display_name || ""}</CardDescription>
                    </div>
                    {warmupBadge(account.warmup?.status || "none")}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-center">
                    <WarmupGauge value={healthScore} />
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Warmup Progress</span>
                      <span>{Math.round(warmupProgress)}%</span>
                    </div>
                    <Progress value={warmupProgress} className="h-2" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Daily Progress</span>
                      <span>{dailySent}/{targetSends}</span>
                    </div>
                    <Progress value={dailyPercent} className="h-2" />
                  </div>
                  {account.progress && account.progress.length > 0 && (
                    <div className="flex items-end gap-1 h-8">
                      {account.progress.slice(-7).map((p: any, i: number) => {
                        const max = Math.max(...account.progress.slice(-7).map((x: any) => x.sent_count || 0), 1)
                        const h = ((p.sent_count || 0) / max) * 100
                        return (
                          <div
                            key={i}
                            className="flex-1 rounded-t bg-primary/60"
                            style={{ height: `${Math.max(h, 4)}%` }}
                            title={`${p.date}: ${p.sent_count || 0} sent`}
                          />
                        )
                      })}
                    </div>
                  )}
                  <div className="flex justify-center pt-1">
                    {account.warmup?.status === "none" || !account.warmup ? (
                      <Button size="sm" variant="outline" onClick={() => openConfig(account)}>
                        <Settings className="h-3.5 w-3.5 mr-1" /> Configure
                      </Button>
                    ) : (
                      <Button size="sm" variant="outline" onClick={() => openConfig(account)}>
                        <Settings className="h-3.5 w-3.5 mr-1" /> Adjust
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" /> Recent Warmup Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : accounts.flatMap((a: any) => a.progress || []).length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <BarChart3 className="h-10 w-10 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">No warmup activity yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Sent</TableHead>
                    <TableHead>Opens</TableHead>
                    <TableHead>Replies</TableHead>
                    <TableHead>Spam</TableHead>
                    <TableHead>Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {accounts.flatMap((account: any) =>
                    (account.progress || []).map((entry: any) => (
                      <TableRow key={entry.id}>
                        <TableCell className="font-medium">{account.email}</TableCell>
                        <TableCell>{formatDate(entry.date)}</TableCell>
                        <TableCell>{entry.sent_count ?? 0}</TableCell>
                        <TableCell>{entry.open_count ?? 0}</TableCell>
                        <TableCell>{entry.reply_count ?? 0}</TableCell>
                        <TableCell>
                          <span className={cn((entry.spam_count ?? 0) > 0 ? "text-red-500" : "text-green-500")}>
                            {entry.spam_count ?? 0}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className={cn(
                            "font-medium",
                            entry.score >= 70 ? "text-green-500" : entry.score >= 40 ? "text-yellow-500" : "text-red-500"
                          )}>
                            {entry.score ?? 0}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={configOpen} onOpenChange={setConfigOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Configure Warmup</DialogTitle>
            <DialogDescription>
              {configAccount ? `Set warmup parameters for ${configAccount.email}` : ""}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <div className="space-y-2">
              <Label>Target Daily Sends: {targetDaily}</Label>
              <input
                type="range"
                min="10"
                max="500"
                step="10"
                value={targetDaily}
                onChange={(e) => setTargetDaily(parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>10</span>
                <span>500</span>
              </div>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Current Level</p>
              <p className="text-2xl font-bold">{targetDaily} emails/day</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfigOpen(false)}>Cancel</Button>
            <Button onClick={handleConfigure} disabled={configuring}>
              <Play className="h-4 w-4 mr-2" />
              {configuring ? "Starting..." : "Start Warmup"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
