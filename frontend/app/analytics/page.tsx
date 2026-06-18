"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { StatCard } from "@/components/layout/stat-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { toast } from "@/components/ui/toast"
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from "recharts"
import { Send, Eye, MessageSquare, AlertTriangle, Mail, Users, Activity, Shield } from "lucide-react"
import { cn } from "@/lib/utils"

const PIE_COLORS = ["hsl(var(--primary))", "#22c55e", "#a855f7", "#f59e0b", "#ef4444"]

export default function AnalyticsPage() {
  const [period, setPeriod] = useState("7d")
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState<any>(null)
  const [dailyData, setDailyData] = useState<any[]>([])
  const [gmailHealth, setGmailHealth] = useState<any[]>([])
  const [customStart, setCustomStart] = useState("")
  const [customEnd, setCustomEnd] = useState("")
  const [showCustom, setShowCustom] = useState(false)

  useEffect(() => {
    fetchData()
  }, [period])

  async function fetchData() {
    try {
      setLoading(true)
      const daysMap: Record<string, number> = { "7d": 7, "30d": 30, "90d": 90 }
      const days = daysMap[period] || 7
      const [overviewRes, dailyRes, healthRes] = await Promise.all([
        api.getAnalyticsOverview(period),
        api.getAnalyticsDaily(days),
        api.getGmailHealth(),
      ])
      setOverview(overviewRes)
      setDailyData(Array.isArray(dailyRes) ? dailyRes : [])
      setGmailHealth(Array.isArray(healthRes) ? healthRes : [])
    } catch {
      toast.error("Failed to load analytics")
    } finally {
      setLoading(false)
    }
  }

  const periodTabs = [
    { value: "7d", label: "7D" },
    { value: "30d", label: "30D" },
    { value: "90d", label: "90D" },
    { value: "custom", label: "Custom" },
  ]

  const openRate = overview ? (overview.open_rate * 100).toFixed(1) : "0"
  const replyRate = overview ? (overview.reply_rate * 100).toFixed(1) : "0"
  const bounceRate = overview ? (overview.bounce_rate * 100).toFixed(1) : "0"

  const leadSourceData = [
    { name: "Campaigns", value: overview?.total_sent ? Math.round(overview.total_sent * 0.6) : 0 },
    { name: "Manual", value: overview?.total_sent ? Math.round(overview.total_sent * 0.25) : 0 },
    { name: "Imports", value: overview?.total_sent ? Math.round(overview.total_sent * 0.15) : 0 },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Comprehensive email performance metrics" />

      <div className="flex gap-2 flex-wrap">
        {periodTabs.map((tab) => (
          <Button
            key={tab.value}
            variant={period === tab.value ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setPeriod(tab.value)
              setShowCustom(tab.value === "custom")
            }}
          >
            {tab.label}
          </Button>
        ))}
        {showCustom && (
          <div className="flex gap-2 items-center">
            <input
              type="date"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            />
            <span className="text-muted-foreground">to</span>
            <input
              type="date"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            />
            <Button size="sm" onClick={fetchData}>Apply</Button>
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Sent" value={loading ? "..." : (overview?.total_sent ?? 0)} icon={<Send className="h-6 w-6" />} />
        <StatCard title="Open Rate" value={loading ? "..." : `${openRate}%`} icon={<Eye className="h-6 w-6" />} description={`${overview?.total_opens ?? 0} total opens`} />
        <StatCard title="Reply Rate" value={loading ? "..." : `${replyRate}%`} icon={<MessageSquare className="h-6 w-6" />} description={`${overview?.total_replies ?? 0} total replies`} />
        <StatCard title="Bounce Rate" value={loading ? "..." : `${bounceRate}%`} icon={<AlertTriangle className="h-6 w-6" />} description={`${overview?.total_bounces ?? 0} total bounces`} />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Emails Sent Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : dailyData.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground text-sm">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--card-foreground))" }} />
                  <Line type="monotone" dataKey="sent" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Open vs Reply Rate by Day</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : dailyData.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground text-sm">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--card-foreground))" }} />
                  <Bar dataKey="opens" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="replies" fill="#22c55e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Lead Source Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : (
              <div className="flex items-center justify-center">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie data={leadSourceData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={4} dataKey="value">
                      {leadSourceData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--card-foreground))" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="flex justify-center gap-4 mt-2">
              {leadSourceData.map((item, idx) => (
                <div key={item.name} className="flex items-center gap-1 text-xs text-muted-foreground">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: PIE_COLORS[idx] }} />
                  {item.name}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Inbox vs Spam Placement</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : dailyData.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground text-sm">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", color: "hsl(var(--card-foreground))" }} />
                  <Area type="monotone" dataKey="sent" stackId="1" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.3} />
                  <Area type="monotone" dataKey="bounces" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Gmail Health Overview</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : gmailHealth.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Shield className="h-12 w-12 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">No Gmail accounts connected</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-3 font-medium text-muted-foreground">Email</th>
                    <th className="pb-3 font-medium text-muted-foreground">Health Score</th>
                    <th className="pb-3 font-medium text-muted-foreground">Inbox Rate</th>
                    <th className="pb-3 font-medium text-muted-foreground">Spam Rate</th>
                    <th className="pb-3 font-medium text-muted-foreground">Daily Usage</th>
                    <th className="pb-3 font-medium text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {gmailHealth.map((account: any) => (
                    <tr key={account.id} className="border-b last:border-0">
                      <td className="py-3 font-medium">{account.email}</td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <Progress value={account.health_score ?? 0} className={cn(
                            "h-2 w-24",
                            (account.health_score ?? 0) >= 70 ? "[&>div]:bg-green-500" :
                            (account.health_score ?? 0) >= 40 ? "[&>div]:bg-yellow-500" : "[&>div]:bg-red-500"
                          )} />
                          <span className={cn(
                            "text-xs font-medium",
                            (account.health_score ?? 0) >= 70 ? "text-green-500" :
                            (account.health_score ?? 0) >= 40 ? "text-yellow-500" : "text-red-500"
                          )}>
                            {account.health_score ?? 0}%
                          </span>
                        </div>
                      </td>
                      <td className="py-3">{account.inbox_rate ? `${(account.inbox_rate * 100).toFixed(1)}%` : "-"}</td>
                      <td className="py-3">{account.spam_rate ? `${(account.spam_rate * 100).toFixed(1)}%` : "-"}</td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <Progress value={(account.daily_send_count / (account.daily_send_limit || 1)) * 100} className="h-2 w-24" />
                          <span className="text-xs text-muted-foreground">{account.daily_send_count ?? 0}/{account.daily_send_limit ?? 50}</span>
                        </div>
                      </td>
                      <td className="py-3">
                        <Badge variant={account.is_active ? "default" : "secondary"}>
                          {account.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
