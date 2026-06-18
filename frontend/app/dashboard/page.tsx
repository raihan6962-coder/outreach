"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { StatCard } from "@/components/layout/stat-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Users, Send, MailCheck, MailX, Inbox as InboxIcon, AlertTriangle, Eye, MessageSquare } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState<any>(null)
  const [dailyData, setDailyData] = useState<any[]>([])
  const [gmailHealth, setGmailHealth] = useState<any[]>([])
  const [period, setPeriod] = useState("daily")

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const [overviewRes, healthRes] = await Promise.all([
          api.getAnalyticsOverview(period),
          api.getGmailHealth(),
        ])
        setOverview(overviewRes)
        setGmailHealth(healthRes)

        let daily: any[] = []
        if (period === "daily") daily = await api.getAnalyticsDaily(7)
        else if (period === "weekly") daily = await api.getAnalyticsWeekly(4)
        else daily = await api.getAnalyticsMonthly(3)
        setDailyData(daily)
      } catch (err) {
        console.error("Failed to fetch dashboard data", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [period])

  const stats = [
    { title: "Total Leads", value: overview?.total_leads ?? 0, icon: <Users className="h-6 w-6" /> },
    { title: "Emails Sent", value: overview?.total_sent ?? 0, icon: <Send className="h-6 w-6" /> },
    { title: "Valid Emails", value: overview?.total_opens ?? 0, icon: <MailCheck className="h-6 w-6" /> },
    { title: "Invalid Emails", value: overview?.total_bounces ?? 0, icon: <MailX className="h-6 w-6" /> },
    { title: "Inbox Rate", value: overview ? `${((1 - (overview.total_bounces / (overview.total_sent || 1))) * 100).toFixed(1)}%` : "0%", icon: <InboxIcon className="h-6 w-6" /> },
    { title: "Spam Rate", value: overview ? `${((overview.total_bounces / (overview.total_sent || 1)) * 100).toFixed(1)}%` : "0%", icon: <AlertTriangle className="h-6 w-6" /> },
    { title: "Open Rate", value: overview ? `${(overview.open_rate * 100).toFixed(1)}%` : "0%", icon: <Eye className="h-6 w-6" /> },
    { title: "Reply Rate", value: overview ? `${(overview.reply_rate * 100).toFixed(1)}%` : "0%", icon: <MessageSquare className="h-6 w-6" /> },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" />

      <Tabs value={period} onValueChange={setPeriod}>
        <TabsList>
          <TabsTrigger value="daily">Daily</TabsTrigger>
          <TabsTrigger value="weekly">Weekly</TabsTrigger>
          <TabsTrigger value="monthly">Monthly</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.title} title={stat.title} value={loading ? "..." : stat.value} icon={stat.icon} />
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Emails Sent Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey={period === "daily" ? "date" : period === "weekly" ? "week" : "month"} stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      color: "hsl(var(--card-foreground))",
                    }}
                  />
                  <Line type="monotone" dataKey="sent" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="opens" stroke="#22c55e" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="replies" stroke="#a855f7" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Gmail Health Scores</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 w-full" />
                ))}
              </div>
            ) : gmailHealth.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-12">No Gmail accounts connected</p>
            ) : (
              <div className="space-y-4">
                {gmailHealth.map((account: any) => (
                  <div key={account.id} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{account.email}</span>
                      <span className={account.health_score >= 70 ? "text-green-500" : account.health_score >= 40 ? "text-yellow-500" : "text-red-500"}>{account.health_score ?? 0}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-secondary overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          (account.health_score ?? 0) >= 70 ? "bg-green-500" : (account.health_score ?? 0) >= 40 ? "bg-yellow-500" : "bg-red-500"
                        }`}
                        style={{ width: `${account.health_score ?? 0}%` }}
                      />
                    </div>
                    <div className="flex gap-3 text-xs text-muted-foreground">
                      <span>Sent: {account.total_sent ?? 0}</span>
                      <span>Replies: {account.total_replies ?? 0}</span>
                      <span>Bounces: {account.total_bounces ?? 0}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
