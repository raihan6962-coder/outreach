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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Play, Pause, RotateCcw, Calendar, Users, Send, Clock } from "lucide-react"
import { formatDate } from "@/lib/utils"

const statusColors: Record<string, string> = {
  draft: "bg-gray-500",
  running: "bg-green-500",
  paused: "bg-yellow-500",
  completed: "bg-blue-500",
  failed: "bg-red-500",
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [step, setStep] = useState(0)
  const [sheets, setSheets] = useState<any[]>([])
  const [templates, setTemplates] = useState<any[]>([])
  const [accounts, setAccounts] = useState<any[]>([])
  const [form, setForm] = useState({
    name: "",
    sheet_source_id: "",
    template_id: "",
    daily_limit: "50",
    sending_start: "09:00",
    sending_end: "17:00",
    timezone: "UTC",
    min_delay: "30",
    max_delay: "120",
    gmail_ids: [] as string[],
  })

  const fetchCampaigns = async () => {
    try {
      setLoading(true)
      const data = await api.getCampaigns()
      setCampaigns(data)
    } catch (err) {
      console.error("Failed to fetch campaigns", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const openCreate = async () => {
    try {
      const [s, t, a] = await Promise.all([
        api.getSheetSources(),
        api.getTemplates(),
        api.getGmailAccounts(),
      ])
      setSheets(s)
      setTemplates(t)
      setAccounts(a)
    } catch (err) {
      console.error("Failed to load form data", err)
    }
    setForm({ name: "", sheet_source_id: "", template_id: "", daily_limit: "50", sending_start: "09:00", sending_end: "17:00", timezone: "UTC", min_delay: "30", max_delay: "120", gmail_ids: [] })
    setStep(0)
    setCreateOpen(true)
  }

  const handleCreate = async () => {
    try {
      await api.createCampaign({
        name: form.name,
        sheet_source_id: form.sheet_source_id,
        template_id: form.template_id,
        settings: {
          daily_send_limit: parseInt(form.daily_limit),
          sending_window_start: form.sending_start,
          sending_window_end: form.sending_end,
          timezone: form.timezone,
          min_delay_seconds: parseInt(form.min_delay),
          max_delay_seconds: parseInt(form.max_delay),
        },
        gmail_account_ids: form.gmail_ids,
      })
      setCreateOpen(false)
      fetchCampaigns()
    } catch (err) {
      console.error("Failed to create campaign", err)
    }
  }

  const handleAction = async (id: string, action: "start" | "pause" | "resume") => {
    try {
      if (action === "start") await api.startCampaign(id)
      else if (action === "pause") await api.pauseCampaign(id)
      else await api.resumeCampaign(id)
      fetchCampaigns()
    } catch (err) {
      console.error(`Failed to ${action} campaign`, err)
    }
  }

  const toggleGmail = (id: string) => {
    setForm((prev) => ({
      ...prev,
      gmail_ids: prev.gmail_ids.includes(id) ? prev.gmail_ids.filter((g) => g !== id) : [...prev.gmail_ids, id],
    }))
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Campaigns"
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4 mr-2" /> Create Campaign
          </Button>
        }
      />

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-2 w-full" />
                <Skeleton className="h-8 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : campaigns.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Send className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-1">No campaigns yet</h3>
            <p className="text-sm text-muted-foreground mb-4">Create your first campaign to start sending emails.</p>
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4 mr-2" /> Create Campaign
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {campaigns.map((campaign) => {
            const progress = campaign.total_leads > 0 ? Math.round((campaign.sent_count / campaign.total_leads) * 100) : 0
            const isRunning = campaign.status === "running"
            const isPaused = campaign.status === "paused"

            return (
              <Card key={campaign.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{campaign.name}</CardTitle>
                      <CardDescription>{campaign.description}</CardDescription>
                    </div>
                    <Badge className={`${statusColors[campaign.status] ?? "bg-gray-500"} text-white`}>
                      {campaign.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1"><Users className="h-3.5 w-3.5" />{campaign.sent_count}/{campaign.total_leads}</span>
                    <span className="flex items-center gap-1"><Send className="h-3.5 w-3.5" />{campaign.open_count} opens</span>
                    <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{campaign.reply_count} replies</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Progress</span>
                      <span>{progress}%</span>
                    </div>
                    <Progress value={progress} className="h-2" />
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(campaign.created_at)}</span>
                    <span className="flex items-center gap-1">{campaign.gmail_account_ids?.length ?? 0} accounts</span>
                  </div>
                  <div className="flex gap-2 pt-1">
                    {campaign.status === "draft" && (
                      <Button size="sm" onClick={() => handleAction(campaign.id, "start")}>
                        <Play className="h-3.5 w-3.5 mr-1" /> Start
                      </Button>
                    )}
                    {isRunning && (
                      <Button size="sm" variant="outline" onClick={() => handleAction(campaign.id, "pause")}>
                        <Pause className="h-3.5 w-3.5 mr-1" /> Pause
                      </Button>
                    )}
                    {isPaused && (
                      <Button size="sm" onClick={() => handleAction(campaign.id, "resume")}>
                        <RotateCcw className="h-3.5 w-3.5 mr-1" /> Resume
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Campaign</DialogTitle>
            <DialogDescription>Step {step + 1} of 3</DialogDescription>
          </DialogHeader>

          <Tabs value={String(step)} onValueChange={(v) => setStep(parseInt(v))}>
            <TabsList className="grid grid-cols-3">
              <TabsTrigger value="0">Basic Info</TabsTrigger>
              <TabsTrigger value="1">Settings</TabsTrigger>
              <TabsTrigger value="2">Gmail Pool</TabsTrigger>
            </TabsList>

            <TabsContent value="0" className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="name">Campaign Name</Label>
                <Input id="name" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} placeholder="My Campaign" />
              </div>
              <div className="space-y-2">
                <Label>Sheet Source</Label>
                <Select value={form.sheet_source_id} onValueChange={(v) => setForm((p) => ({ ...p, sheet_source_id: v }))}>
                  <SelectTrigger><SelectValue placeholder="Select sheet source" /></SelectTrigger>
                  <SelectContent>
                    {sheets.map((s: any) => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Template</Label>
                <Select value={form.template_id} onValueChange={(v) => setForm((p) => ({ ...p, template_id: v }))}>
                  <SelectTrigger><SelectValue placeholder="Select template" /></SelectTrigger>
                  <SelectContent>
                    {templates.map((t: any) => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>

            <TabsContent value="1" className="space-y-4 pt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="daily_limit">Daily Limit</Label>
                  <Input id="daily_limit" type="number" value={form.daily_limit} onChange={(e) => setForm((p) => ({ ...p, daily_limit: e.target.value }))} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Input id="timezone" value={form.timezone} onChange={(e) => setForm((p) => ({ ...p, timezone: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sending_start">Window Start</Label>
                  <Input id="sending_start" type="time" value={form.sending_start} onChange={(e) => setForm((p) => ({ ...p, sending_start: e.target.value }))} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sending_end">Window End</Label>
                  <Input id="sending_end" type="time" value={form.sending_end} onChange={(e) => setForm((p) => ({ ...p, sending_end: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="min_delay">Min Delay (sec)</Label>
                  <Input id="min_delay" type="number" value={form.min_delay} onChange={(e) => setForm((p) => ({ ...p, min_delay: e.target.value }))} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_delay">Max Delay (sec)</Label>
                  <Input id="max_delay" type="number" value={form.max_delay} onChange={(e) => setForm((p) => ({ ...p, max_delay: e.target.value }))} />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="2" className="space-y-4 pt-4">
              <p className="text-sm text-muted-foreground">Select Gmail accounts to use for this campaign.</p>
              {accounts.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No Gmail accounts found. Connect one first.</p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {accounts.map((acc: any) => (
                    <label key={acc.id} className="flex items-center gap-3 p-2 rounded-md hover:bg-accent cursor-pointer">
                      <Checkbox checked={form.gmail_ids.includes(acc.id)} onCheckedChange={() => toggleGmail(acc.id)} />
                      <div className="text-sm">
                        <p className="font-medium">{acc.email}</p>
                        <p className="text-xs text-muted-foreground">{acc.is_active ? "Active" : "Inactive"} &middot; {acc.daily_send_count}/{acc.daily_send_limit} sent today</p>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>

          <DialogFooter className="flex justify-between">
            <div>
              {step > 0 && <Button variant="outline" onClick={() => setStep((p) => p - 1)}>Previous</Button>}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              {step < 2 ? (
                <Button onClick={() => setStep((p) => p + 1)}>Next</Button>
              ) : (
                <Button onClick={handleCreate}>Create Campaign</Button>
              )}
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
