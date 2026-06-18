"use client"

import { useState, useEffect, useRef } from "react"
import { api } from "@/lib/api-client"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Plus, MoreHorizontal, Copy, Pencil, Trash2, Send, FolderPlus, Eye, Variable, FileText } from "lucide-react"
import { formatDate } from "@/lib/utils"

const TEMPLATE_VARIABLES = ["{{first_name}}", "{{last_name}}", "{{app_name}}", "{{developer}}", "{{company}}", "{{email}}", "{{date}}"]

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<any[]>([])
  const [folders, setFolders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<any>(null)
  const [folderDialogOpen, setFolderDialogOpen] = useState(false)
  const [newFolderName, setNewFolderName] = useState("")
  const [testSendOpen, setTestSendOpen] = useState(false)
  const [testSendEmail, setTestSendEmail] = useState("")
  const [testSendTemplateId, setTestSendTemplateId] = useState<string | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewHtml, setPreviewHtml] = useState("")
  const bodyRef = useRef<HTMLTextAreaElement>(null)

  const [form, setForm] = useState({
    name: "",
    folder_id: "",
    subject: "",
    body_html: "",
    body_text: "",
  })
  const [activeTab, setActiveTab] = useState("html")

  const fetchData = async () => {
    try {
      setLoading(true)
      const [t, f] = await Promise.all([
        api.getTemplates(),
        api.getTemplateFolders(),
      ])
      setTemplates(t)
      setFolders(f)
    } catch (err) {
      console.error("Failed to fetch templates", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const filteredTemplates = selectedFolder
    ? templates.filter((t) => t.folder_id === selectedFolder)
    : templates

  const resetForm = () => {
    setForm({ name: "", folder_id: "", subject: "", body_html: "", body_text: "" })
    setActiveTab("html")
  }

  const openCreate = () => {
    resetForm()
    setEditingTemplate(null)
    setCreateOpen(true)
  }

  const openEdit = (template: any) => {
    setEditingTemplate(template)
    setForm({
      name: template.name,
      folder_id: template.folder_id ?? "",
      subject: template.subject,
      body_html: template.body,
      body_text: template.body,
    })
    setCreateOpen(true)
  }

  const insertVariable = (variable: string) => {
    const textarea = bodyRef.current
    if (!textarea) return
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const field = activeTab === "html" ? "body_html" : "body_text"
    const current = form[field as keyof typeof form] as string
    const updated = current.slice(0, start) + variable + current.slice(end)
    setForm((prev) => ({ ...prev, [field]: updated }))
    setTimeout(() => {
      textarea.focus()
      textarea.selectionStart = textarea.selectionEnd = start + variable.length
    }, 0)
  }

  const handleSave = async () => {
    const body = activeTab === "html" ? form.body_html : form.body_text
    try {
      if (editingTemplate) {
        await api.updateTemplate(editingTemplate.id, { ...form, body })
      } else {
        await api.createTemplate({ ...form, body })
      }
      setCreateOpen(false)
      resetForm()
      fetchData()
    } catch (err) {
      console.error("Failed to save template", err)
    }
  }

  const handleDuplicate = async (id: string) => {
    try {
      await api.duplicateTemplate(id)
      fetchData()
    } catch (err) {
      console.error("Failed to duplicate template", err)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await api.deleteTemplate(id)
      fetchData()
    } catch (err) {
      console.error("Failed to delete template", err)
    }
  }

  const handlePreview = () => {
    const body = activeTab === "html" ? form.body_html : form.body_text
    const rendered = body
      .replace(/\{\{first_name\}\}/g, "John")
      .replace(/\{\{last_name\}\}/g, "Doe")
      .replace(/\{\{app_name\}\}/g, "MyApp")
      .replace(/\{\{developer\}\}/g, "Developer Name")
      .replace(/\{\{company\}\}/g, "Acme Inc")
      .replace(/\{\{email\}\}/g, "john@example.com")
      .replace(/\{\{date\}\}/g, new Date().toLocaleDateString())
    setPreviewHtml(rendered)
    setPreviewOpen(true)
  }

  const handleTestSend = async () => {
    if (!testSendTemplateId || !testSendEmail) return
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/templates/${testSendTemplateId}/test-send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ email: testSendEmail }),
      })
      setTestSendOpen(false)
      setTestSendEmail("")
    } catch (err) {
      console.error("Failed to send test email", err)
    }
  }

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return
    try {
      await api.createTemplateFolder({ name: newFolderName })
      setFolderDialogOpen(false)
      setNewFolderName("")
      fetchData()
    } catch (err) {
      console.error("Failed to create folder", err)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Email Templates"
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4 mr-2" /> Create Template
          </Button>
        }
      />

      <div className="flex gap-6">
        <div className="w-56 shrink-0 space-y-2">
          <div className="space-y-1">
            <Button
              variant={selectedFolder === null ? "secondary" : "ghost"}
              className="w-full justify-start"
              onClick={() => setSelectedFolder(null)}
            >
              All Templates
            </Button>
            {folders.map((folder: any) => (
              <Button
                key={folder.id}
                variant={selectedFolder === folder.id ? "secondary" : "ghost"}
                className="w-full justify-start"
                onClick={() => setSelectedFolder(folder.id)}
              >
                {folder.name}
              </Button>
            ))}
          </div>
          <Separator />
          <Button variant="ghost" size="sm" className="w-full justify-start" onClick={() => setFolderDialogOpen(true)}>
            <FolderPlus className="h-4 w-4 mr-2" /> New Folder
          </Button>
        </div>

        <div className="flex-1">
          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-24" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-4 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredTemplates.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-1">No templates yet</h3>
                <p className="text-sm text-muted-foreground mb-4">Create your first email template.</p>
                <Button onClick={openCreate}>
                  <Plus className="h-4 w-4 mr-2" /> Create Template
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredTemplates.map((template) => (
                <Card key={template.id} className="group">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base truncate">{template.name}</CardTitle>
                        <CardDescription className="truncate">{template.subject}</CardDescription>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEdit(template)}>
                            <Pencil className="h-4 w-4 mr-2" /> Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDuplicate(template.id)}>
                            <Copy className="h-4 w-4 mr-2" /> Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDelete(template.id)} className="text-destructive">
                            <Trash2 className="h-4 w-4 mr-2" /> Delete
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              setTestSendTemplateId(template.id)
                              setTestSendOpen(true)
                            }}
                          >
                            <Send className="h-4 w-4 mr-2" /> Test Send
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      {template.folder_id && (
                        <Badge variant="outline" className="text-xs">
                          {folders.find((f) => f.id === template.folder_id)?.name ?? "Unknown"}
                        </Badge>
                      )}
                      <span>{formatDate(template.created_at)}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingTemplate ? "Edit Template" : "Create Template"}</DialogTitle>
            <DialogDescription>Fill in the template details below.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="tpl_name">Name</Label>
                <Input id="tpl_name" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Folder</Label>
                <Select value={form.folder_id} onValueChange={(v) => setForm((p) => ({ ...p, folder_id: v }))}>
                  <SelectTrigger><SelectValue placeholder="No folder" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No folder</SelectItem>
                    {folders.map((f: any) => (
                      <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="tpl_subject">Subject</Label>
              <Input id="tpl_subject" value={form.subject} onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Body</Label>
                <div className="flex items-center gap-1">
                  {TEMPLATE_VARIABLES.map((v) => (
                    <Button key={v} variant="outline" size="sm" className="h-7 text-xs px-2" onClick={() => insertVariable(v)}>
                      <Variable className="h-3 w-3 mr-1" />{v.replace(/[{}]/g, "")}
                    </Button>
                  ))}
                </div>
              </div>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                  <TabsTrigger value="html">HTML</TabsTrigger>
                  <TabsTrigger value="text">Plain Text</TabsTrigger>
                </TabsList>
                <TabsContent value="html">
                  <textarea
                    ref={bodyRef}
                    className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    value={form.body_html}
                    onChange={(e) => setForm((p) => ({ ...p, body_html: e.target.value }))}
                    placeholder="<html><body><p>Hello {{first_name}},</p></body></html>"
                  />
                </TabsContent>
                <TabsContent value="text">
                  <textarea
                    ref={bodyRef}
                    className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    value={form.body_text}
                    onChange={(e) => setForm((p) => ({ ...p, body_text: e.target.value }))}
                    placeholder="Hello {{first_name}},"
                  />
                </TabsContent>
              </Tabs>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handlePreview}>
              <Eye className="h-4 w-4 mr-2" /> Preview
            </Button>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleSave}>{editingTemplate ? "Save" : "Create"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Template Preview</DialogTitle>
          </DialogHeader>
          <div className="rounded-md border p-4 bg-background">
            {activeTab === "html" ? (
              <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
            ) : (
              <pre className="whitespace-pre-wrap text-sm font-mono">{previewHtml}</pre>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={testSendOpen} onOpenChange={setTestSendOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Test Send</DialogTitle>
            <DialogDescription>Send a test email to verify your template.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="test_email">Recipient Email</Label>
            <Input id="test_email" type="email" value={testSendEmail} onChange={(e) => setTestSendEmail(e.target.value)} placeholder="you@example.com" />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTestSendOpen(false)}>Cancel</Button>
            <Button onClick={handleTestSend}>
              <Send className="h-4 w-4 mr-2" /> Send Test
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={folderDialogOpen} onOpenChange={setFolderDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Folder</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="folder_name">Folder Name</Label>
            <Input id="folder_name" value={newFolderName} onChange={(e) => setNewFolderName(e.target.value)} placeholder="My Folder" />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFolderDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateFolder}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}


