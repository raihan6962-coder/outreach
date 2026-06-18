import { API_BASE_URL } from "./constants"

type RequestOptions = {
  method?: string
  body?: any
  headers?: Record<string, string>
  params?: Record<string, string>
}

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor() {
    this.baseUrl = API_BASE_URL
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token")
    }
  }

  setToken(token: string | null) {
    this.token = token
    if (token) localStorage.setItem("access_token", token)
    else localStorage.removeItem("access_token")
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const path = `${this.baseUrl}${endpoint}`
    const url = path.startsWith("http") ? new URL(path) : new URL(path, window.location.origin)
    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => url.searchParams.set(key, value))
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...options.headers,
    }
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`

    const response = await fetch(url.toString(), {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    })

    if (response.status === 401) {
      localStorage.removeItem("access_token")
      window.location.href = "/login"
      throw new Error("Unauthorized")
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }))
      throw new Error(error.detail || "Request failed")
    }

    return response.json()
  }

  async register(data: { email: string; password: string; name: string }) {
    return this.request<{ access_token: string; refresh_token: string }>("/auth/register", {
      method: "POST", body: data,
    })
  }

  async login(data: { email: string; password: string }) {
    return this.request<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST", body: data,
    })
  }

  async getMe() {
    return this.request<any>("/auth/me")
  }

  async getGmailAuthUrl() {
    return this.request<{ auth_url: string }>("/gmail/auth-url")
  }

  async getGmailAccounts() {
    return this.request<any[]>("/gmail/accounts")
  }

  async toggleGmail(id: string, isActive: boolean) {
    return this.request<any>(`/gmail/accounts/${id}/toggle`, {
      method: "PUT", body: { is_active: isActive },
    })
  }

  async disconnectGmail(id: string) {
    return this.request<any>(`/gmail/accounts/${id}`, { method: "DELETE" })
  }

  async getGmailHealth(id: string) {
    return this.request<any>(`/gmail/accounts/${id}/health`)
  }

  async getSheetSources() {
    return this.request<any[]>("/sheets")
  }

  async createSheetSource(data: any) {
    return this.request<any>("/sheets", { method: "POST", body: data })
  }

  async deleteSheetSource(id: string) {
    return this.request<any>(`/sheets/${id}`, { method: "DELETE" })
  }

  async testSheetSource(id: string) {
    return this.request<any>(`/sheets/${id}/test`, { method: "POST" })
  }

  async syncSheetSource(id: string) {
    return this.request<any>(`/sheets/${id}/sync`, { method: "POST" })
  }

  async getLeads(params?: Record<string, string>) {
    return this.request<any>("/leads", { params })
  }

  async updateLead(id: string, data: any) {
    return this.request<any>(`/leads/${id}`, { method: "PUT", body: data })
  }

  async deleteLead(id: string) {
    return this.request<any>(`/leads/${id}`, { method: "DELETE" })
  }

  async updateLeadTags(id: string, tags: string[]) {
    return this.request<any>(`/leads/${id}/tags`, { method: "PUT", body: { tags } })
  }

  async addLeadNote(id: string, notes: string) {
    return this.request<any>(`/leads/${id}/notes`, { method: "POST", body: { notes } })
  }

  async deleteLeadsBulk(leadIds: string[]) {
    return this.request<any>("/leads/bulk", { method: "POST", body: { lead_ids: leadIds, action: "delete" } })
  }

  async getTemplates() {
    return this.request<any[]>("/templates")
  }

  async createTemplate(data: any) {
    return this.request<any>("/templates", { method: "POST", body: data })
  }

  async updateTemplate(id: string, data: any) {
    return this.request<any>(`/templates/${id}`, { method: "PUT", body: data })
  }

  async deleteTemplate(id: string) {
    return this.request<any>(`/templates/${id}`, { method: "DELETE" })
  }

  async duplicateTemplate(id: string) {
    return this.request<any>(`/templates/${id}/duplicate`, { method: "POST" })
  }

  async getTemplateFolders() {
    return this.request<any[]>("/templates/folders")
  }

  async createTemplateFolder(data: any) {
    return this.request<any>("/templates/folders", { method: "POST", body: data })
  }

  async getCampaigns() {
    return this.request<any[]>("/campaigns")
  }

  async getCampaign(id: string) {
    return this.request<any>(`/campaigns/${id}`)
  }

  async createCampaign(data: any) {
    return this.request<any>("/campaigns", { method: "POST", body: data })
  }

  async updateCampaign(id: string, data: any) {
    return this.request<any>(`/campaigns/${id}`, { method: "PUT", body: data })
  }

  async deleteCampaign(id: string) {
    return this.request<any>(`/campaigns/${id}`, { method: "DELETE" })
  }

  async startCampaign(id: string) {
    return this.request<any>(`/campaigns/${id}/start`, { method: "POST" })
  }

  async pauseCampaign(id: string) {
    return this.request<any>(`/campaigns/${id}/pause`, { method: "POST" })
  }

  async resumeCampaign(id: string) {
    return this.request<any>(`/campaigns/${id}/resume`, { method: "POST" })
  }

  async getCampaignStats(id: string) {
    return this.request<any>(`/campaigns/${id}/stats`)
  }

  async getInbox(params?: Record<string, string>) {
    return this.request<any[]>("/inbox", { params })
  }

  async getInboxMessage(id: string) {
    return this.request<any>(`/inbox/${id}`)
  }

  async getInboxReplies(id: string) {
    return this.request<any[]>(`/inbox/${id}/replies`)
  }

  async getPipelineStages() {
    return this.request<any[]>("/pipeline/stages")
  }

  async createPipelineStage(data: any) {
    return this.request<any>("/pipeline/stages", { method: "POST", body: data })
  }

  async moveLeadStage(leadId: string, stageId: string) {
    return this.request<any>(`/pipeline/leads/${leadId}/stage`, {
      method: "PUT", body: { stage_id: stageId },
    })
  }

  async getAnalyticsOverview(period?: string) {
    return this.request<any>("/analytics/overview", {
      params: period ? { period } : undefined,
    })
  }

  async getAnalyticsDaily(days?: number) {
    return this.request<any[]>("/analytics/daily", {
      params: days ? { days: days.toString() } : undefined,
    })
  }

  async getAnalyticsWeekly(weeks?: number) {
    return this.request<any[]>("/analytics/weekly", {
      params: weeks ? { weeks: weeks.toString() } : undefined,
    })
  }

  async getAnalyticsMonthly(months?: number) {
    return this.request<any[]>("/analytics/monthly", {
      params: months ? { months: months.toString() } : undefined,
    })
  }

  async getGmailHealth() {
    return this.request<any[]>("/analytics/gmail-health")
  }

  async analyzeSpam(data: any) {
    return this.request<any>("/spam-test/analyze", { method: "POST", body: data })
  }

  async getSpamTestHistory() {
    return this.request<any[]>("/spam-test/history")
  }

  async getWarmupStatus(gmailId: string) {
    return this.request<any>(`/warmup/status/${gmailId}`)
  }

  async configureWarmup(data: any) {
    return this.request<any>("/warmup/configure", { method: "POST", body: data })
  }

  async getWarmupProgress(gmailId: string) {
    return this.request<any[]>(`/warmup/progress/${gmailId}`)
  }

  async getNotifications() {
    return this.request<any[]>("/notifications")
  }

  async getUnreadCount() {
    return this.request<{ count: number }>("/notifications/unread-count")
  }

  async markNotificationRead(id: string) {
    return this.request<any>(`/notifications/${id}/read`, { method: "PUT" })
  }

  async markAllNotificationsRead() {
    return this.request<any>("/notifications/read-all", { method: "PUT" })
  }

  async updateSettings(data: any) {
    return this.request<any>("/auth/settings", { method: "PUT", body: data })
  }
}

export const api = new ApiClient()
