"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { toast } from "@/components/ui/toast"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Moon, Sun, Monitor, Save, Link2, Trash2, RefreshCw, Wifi, WifiOff, Globe, Bell, User, Palette, Settings as SettingsIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTheme } from "next-themes"
import { formatDateTime } from "@/lib/utils"

function ThemeOption({ value, current, label, icon: Icon }: { value: string; current: string; label: string; icon: any }) {
  return (
    <button
      className={cn(
        "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
        current === value ? "border-primary bg-primary/5" : "border-border hover:border-muted-foreground/30"
      )}
      onClick={() => {}}
    >
      <Icon className="h-8 w-8" />
      <span className="text-sm font-medium">{label}</span>
    </button>
  )
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [profile, setProfile] = useState({ name: "", email: "", company: "" })
  const [notifications, setNotifications] = useState({
    email_notifications: true,
    campaign_finished: true,
    gmail_limit_reached: true,
    gmail_disconnected: true,
    new_replies: true,
    bounce_detected: true,
    spam_risk_high: true,
  })
  const [sheets, setSheets] = useState<any[]>([])
  const [addSheetOpen, setAddSheetOpen] = useState(false)
  const [sheetForm, setSheetForm] = useState({ name: "", webhook_url: "" })

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    try {
      setLoading(true)
      const [me, sheetSources] = await Promise.all([
        api.getMe(),
        api.getSheetSources(),
      ])
      setProfile({ name: me.name || "", email: me.email || "", company: me.settings?.company || "" })
      setSheets(Array.isArray(sheetSources) ? sheetSources : [])
    } catch {
      toast.error("Failed to load settings")
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveProfile() {
    try {
      setSaving(true)
      await api.updateSettings({ name: profile.name, company: profile.company })
      toast.success("Profile updated")
    } catch {
      toast.error("Failed to update profile")
    } finally {
      setSaving(false)
    }
  }

  async function handleSaveNotifications() {
    try {
      setSaving(true)
      await api.updateSettings(notifications)
      toast.success("Notification preferences saved")
    } catch {
      toast.error("Failed to save notifications")
    } finally {
      setSaving(false)
    }
  }

  async function handleAddSheet() {
    if (!sheetForm.name || !sheetForm.webhook_url) {
      toast.error("Name and URL are required")
      return
    }
    try {
      await api.createSheetSource(sheetForm)
      toast.success("Sheet source added")
      setAddSheetOpen(false)
      setSheetForm({ name: "", webhook_url: "" })
      const sheets = await api.getSheetSources()
      setSheets(Array.isArray(sheets) ? sheets : [])
    } catch {
      toast.error("Failed to add sheet source")
    }
  }

  async function handleTestSheet(id: string) {
    try {
      await api.testSheetSource(id)
      toast.success("Test successful")
    } catch {
      toast.error("Test failed")
    }
  }

  async function handleSyncSheet(id: string) {
    try {
      await api.syncSheetSource(id)
      toast.success("Sync started")
    } catch {
      toast.error("Sync failed")
    }
  }

  async function handleDeleteSheet(id: string) {
    try {
      await api.deleteSheetSource(id)
      toast.success("Sheet source deleted")
      const sheets = await api.getSheetSources()
      setSheets(Array.isArray(sheets) ? sheets : [])
    } catch {
      toast.error("Failed to delete sheet source")
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Manage your account and preferences" />

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile"><User className="h-4 w-4 mr-2" /> Profile</TabsTrigger>
          <TabsTrigger value="appearance"><Palette className="h-4 w-4 mr-2" /> Appearance</TabsTrigger>
          <TabsTrigger value="notifications"><Bell className="h-4 w-4 mr-2" /> Notifications</TabsTrigger>
          <TabsTrigger value="integrations"><Link2 className="h-4 w-4 mr-2" /> Integrations</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>Update your personal details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="name">Name</Label>
                    <Input id="name" value={profile.name} onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" value={profile.email} disabled />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="company">Company</Label>
                    <Input id="company" value={profile.company} onChange={(e) => setProfile((p) => ({ ...p, company: e.target.value }))} placeholder="Your company name" />
                  </div>
                  <Button onClick={handleSaveProfile} disabled={saving}>
                    <Save className="h-4 w-4 mr-2" />
                    {saving ? "Saving..." : "Save Changes"}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
              <CardDescription>Choose your preferred appearance</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex gap-4">
                  <Skeleton className="h-28 w-28" />
                  <Skeleton className="h-28 w-28" />
                  <Skeleton className="h-28 w-28" />
                </div>
              ) : (
                <div className="flex gap-4 flex-wrap">
                  {[
                    { value: "light", label: "Light", icon: Sun },
                    { value: "dark", label: "Dark", icon: Moon },
                    { value: "system", label: "System", icon: Monitor },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      className={cn(
                        "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
                        theme === opt.value ? "border-primary bg-primary/5" : "border-border hover:border-muted-foreground/30"
                      )}
                      onClick={() => setTheme(opt.value)}
                    >
                      <opt.icon className="h-8 w-8" />
                      <span className="text-sm font-medium">{opt.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Control which notifications you receive</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {Array.from({ length: 7 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {[
                    { key: "email_notifications", label: "Email Notifications" },
                    { key: "campaign_finished", label: "Campaign Finished" },
                    { key: "gmail_limit_reached", label: "Gmail Limit Reached" },
                    { key: "gmail_disconnected", label: "Gmail Disconnected" },
                    { key: "new_replies", label: "New Replies" },
                    { key: "bounce_detected", label: "Bounce Detected" },
                    { key: "spam_risk_high", label: "Spam Risk High" },
                  ].map((item) => (
                    <div key={item.key} className="flex items-center justify-between">
                      <Label htmlFor={item.key} className="cursor-pointer">{item.label}</Label>
                      <Switch
                        id={item.key}
                        checked={(notifications as any)[item.key]}
                        onCheckedChange={(checked) => setNotifications((prev) => ({ ...prev, [item.key]: checked }))}
                      />
                    </div>
                  ))}
                  <Separator />
                  <Button onClick={handleSaveNotifications} disabled={saving}>
                    <Save className="h-4 w-4 mr-2" />
                    {saving ? "Saving..." : "Save Preferences"}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Google Sheet Webhooks</CardTitle>
                  <CardDescription>Manage your sheet integration sources</CardDescription>
                </div>
                <Button size="sm" onClick={() => setAddSheetOpen(true)}>
                  <Link2 className="h-4 w-4 mr-2" /> Add Sheet URL
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : sheets.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Globe className="h-12 w-12 text-muted-foreground mb-3" />
                  <p className="text-sm text-muted-foreground mb-2">No sheet integrations configured</p>
                  <Button variant="outline" size="sm" onClick={() => setAddSheetOpen(true)}>
                    <Link2 className="h-4 w-4 mr-2" /> Add Sheet URL
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {sheets.map((sheet: any) => (
                    <div key={sheet.id} className="flex items-center justify-between p-3 rounded-lg border">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-sm truncate">{sheet.name}</p>
                          <Badge variant={sheet.is_active ? "default" : "secondary"} className="text-xs">
                            {sheet.is_active ? <Wifi className="h-3 w-3 mr-1" /> : <WifiOff className="h-3 w-3 mr-1" />}
                            {sheet.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground truncate mt-0.5">{sheet.webhook_url || sheet.sheet_id || ""}</p>
                        {sheet.last_synced_at && (
                          <p className="text-xs text-muted-foreground mt-0.5">Last synced: {formatDateTime(sheet.last_synced_at)}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-1 shrink-0 ml-3">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleTestSheet(sheet.id)}>
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleSyncSheet(sheet.id)}>
                          <Link2 className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDeleteSheet(sheet.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={addSheetOpen} onOpenChange={setAddSheetOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Sheet Webhook</DialogTitle>
            <DialogDescription>Add a Google Sheet webhook URL to sync data</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="sheet_name">Name</Label>
              <Input id="sheet_name" value={sheetForm.name} onChange={(e) => setSheetForm((p) => ({ ...p, name: e.target.value }))} placeholder="My Sheet" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="webhook_url">Webhook URL</Label>
              <Input id="webhook_url" value={sheetForm.webhook_url} onChange={(e) => setSheetForm((p) => ({ ...p, webhook_url: e.target.value }))} placeholder="https://sheets.googleapis.com/..." />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddSheetOpen(false)}>Cancel</Button>
            <Button onClick={handleAddSheet}>
              <Link2 className="h-4 w-4 mr-2" /> Save & Test
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
