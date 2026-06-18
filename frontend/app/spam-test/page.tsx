"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Shield, AlertTriangle, CheckCircle, Lightbulb, Send, RefreshCw, Clock } from "lucide-react"
import { formatDateTime } from "@/lib/utils"
import { cn } from "@/lib/utils"

function CircularGauge({ value, max = 100, label, color }: { value: number; max?: number; label: string; color: string }) {
  const radius = 60
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(value / max, 1)
  const offset = circumference * (1 - progress)

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="hsl(var(--secondary))" strokeWidth="10" />
        <circle
          cx="70" cy="70" r={radius}
          fill="none" stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
          className="transition-all duration-700"
        />
        <text x="70" y="65" textAnchor="middle" className="text-2xl font-bold" fill="currentColor">{value}</text>
        <text x="70" y="85" textAnchor="middle" className="text-xs fill-muted-foreground">{label}</text>
      </svg>
    </div>
  )
}

export default function SpamTestPage() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [form, setForm] = useState({ gmail_account_id: "", subject: "", body: "" })

  useEffect(() => {
    fetchInitial()
  }, [])

  async function fetchInitial() {
    try {
      setLoading(true)
      const [accts, hist] = await Promise.all([
        api.getGmailAccounts(),
        api.getSpamTestHistory(),
      ])
      setAccounts(accts)
      setHistory(Array.isArray(hist) ? hist : [])
    } catch {
      toast.error("Failed to load spam test data")
    } finally {
      setLoading(false)
    }
  }

  async function handleAnalyze() {
    if (!form.subject || !form.body) {
      toast.error("Subject and body are required")
      return
    }
    try {
      setAnalyzing(true)
      const res = await api.analyzeSpam(form)
      setResult(res)
      const hist = await api.getSpamTestHistory()
      setHistory(Array.isArray(hist) ? hist : [])
      toast.success("Analysis complete")
    } catch {
      toast.error("Analysis failed")
    } finally {
      setAnalyzing(false)
    }
  }

  const spamScore = result?.spam_score ?? 0
  const deliverabilityScore = 100 - spamScore
  const spamColor = spamScore >= 60 ? "#ef4444" : spamScore >= 30 ? "#f59e0b" : "#22c55e"
  const delivColor = deliverabilityScore >= 70 ? "#22c55e" : deliverabilityScore >= 40 ? "#f59e0b" : "#ef4444"
  const riskLevel = spamScore >= 60 ? "High Risk" : spamScore >= 30 ? "Medium Risk" : "Low Risk"
  const riskColor = spamScore >= 60 ? "destructive" : spamScore >= 30 ? "default" : "secondary"
  const riskBg = spamScore >= 60 ? "bg-red-500" : spamScore >= 30 ? "bg-yellow-500" : "bg-green-500"

  const recommendations = result?.details?.recommendations || []

  function getRiskIcon() {
    if (spamScore >= 60) return <AlertTriangle className="h-4 w-4" />
    if (spamScore >= 30) return <Shield className="h-4 w-4" />
    return <CheckCircle className="h-4 w-4" />
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Spam Test Center" description="Analyze emails for spam risk before sending" />

      {loading ? (
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-[400px]" />
          <Skeleton className="h-[400px]" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Test Email</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Sender Account</Label>
                <Select value={form.gmail_account_id} onValueChange={(v) => setForm((p) => ({ ...p, gmail_account_id: v }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select Gmail account" />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts.map((acc: any) => (
                      <SelectItem key={acc.id} value={acc.id}>{acc.email}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="subject">Subject</Label>
                <Input
                  id="subject"
                  value={form.subject}
                  onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))}
                  placeholder="Email subject line"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="body">Email Body</Label>
                <textarea
                  id="body"
                  className="flex min-h-[180px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  value={form.body}
                  onChange={(e) => setForm((p) => ({ ...p, body: e.target.value }))}
                  placeholder="Paste your email content here..."
                />
              </div>
              <Button onClick={handleAnalyze} disabled={analyzing} className="w-full">
                {analyzing ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Send className="h-4 w-4 mr-2" />
                )}
                {analyzing ? "Analyzing..." : "Analyze"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Results</CardTitle>
            </CardHeader>
            <CardContent>
              {analyzing ? (
                <div className="flex flex-col items-center justify-center py-12 gap-4">
                  <RefreshCw className="h-10 w-10 animate-spin text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Analyzing email content...</p>
                </div>
              ) : result ? (
                <div className="space-y-6">
                  <div className="flex justify-center gap-8">
                    <CircularGauge value={Math.round(spamScore)} label="Spam Score" color={spamColor} />
                    <CircularGauge value={Math.round(deliverabilityScore)} label="Deliverability" color={delivColor} />
                  </div>
                  <div className="flex justify-center">
                    <Badge className={`${riskBg} text-white px-4 py-1 text-sm flex items-center gap-1`} variant={riskLevel === "Low Risk" ? "secondary" : "default"}>
                      {getRiskIcon()} {riskLevel}
                    </Badge>
                  </div>
                  {recommendations.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium flex items-center gap-1">
                        <Lightbulb className="h-4 w-4" /> Recommendations
                      </p>
                      <ul className="space-y-1">
                        {recommendations.map((rec: string, i: number) => (
                          <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-primary mt-0.5">&#8226;</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result?.details?.issues && result.details.issues.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-sm font-medium flex items-center gap-1 text-red-500">
                        <AlertTriangle className="h-4 w-4" /> Issues Found
                      </p>
                      {result.details.issues.map((issue: string, i: number) => (
                        <p key={i} className="text-sm text-red-400">- {issue}</p>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <Shield className="h-12 w-12 text-muted-foreground mb-3" />
                  <p className="text-sm text-muted-foreground">Submit an email to see spam analysis results</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5" /> Test History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : history.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <RefreshCw className="h-10 w-10 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">No tests run yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Subject</TableHead>
                    <TableHead>Spam Score</TableHead>
                    <TableHead>Deliverability</TableHead>
                    <TableHead>Risk Level</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.map((test: any) => {
                    const score = test.spam_score ?? 0
                    const deliv = 100 - score
                    const risk = score >= 60 ? "High Risk" : score >= 30 ? "Medium Risk" : "Low Risk"
                    return (
                      <TableRow key={test.id}>
                        <TableCell className="text-sm">{formatDateTime(test.created_at)}</TableCell>
                        <TableCell className="font-medium">{test.subject}</TableCell>
                        <TableCell>
                          <span className={cn("font-medium", score >= 60 ? "text-red-500" : score >= 30 ? "text-yellow-500" : "text-green-500")}>
                            {Math.round(score)}%
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className={cn("font-medium", deliv >= 70 ? "text-green-500" : deliv >= 40 ? "text-yellow-500" : "text-red-500")}>
                            {Math.round(deliv)}%
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={score >= 60 ? "destructive" : score >= 30 ? "default" : "secondary"}
                            className={score >= 60 ? "" : score >= 30 ? "bg-yellow-500 text-white" : ""}
                          >
                            {risk}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
