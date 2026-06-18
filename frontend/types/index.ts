export interface User {
  id: string
  email: string
  name: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string
  settings?: UserSettings
}

export interface UserSettings {
  daily_send_limit?: number
  send_interval_seconds?: number
  timezone?: string
  working_hours_start?: string
  working_hours_end?: string
  working_days?: number[]
  max_daily_leads?: number
  openai_api_key?: string
  follow_up_days?: number[]
}

export interface GmailAccount {
  id: string
  email: string
  user_id: string
  is_active: boolean
  is_authenticated: boolean
  is_primary: boolean
  credentials_updated_at?: string
  history_id?: string
  daily_send_count: number
  daily_send_limit: number
  last_send_reset?: string
  warmup_enabled: boolean
  warmup_status: string
  created_at: string
  updated_at: string
}

export interface SheetSource {
  id: string
  user_id: string
  name: string
  sheet_id: string
  sheet_name: string
  range: string
  column_mapping: Record<string, string>
  last_synced_at?: string
  is_active: boolean
  created_at: string
}

export interface Lead {
  id: string
  user_id: string
  email: string
  first_name?: string
  last_name?: string
  company?: string
  position?: string
  phone?: string
  website?: string
  linkedin_url?: string
  source: string
  tags: string[]
  notes?: string
  validation_status: string
  stage_id?: string
  assigned_campaign_id?: string
  last_contacted_at?: string
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface Template {
  id: string
  user_id: string
  name: string
  subject: string
  body: string
  folder_id?: string
  variables: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TemplateFolder {
  id: string
  user_id: string
  name: string
  parent_id?: string
  created_at: string
}

export interface Campaign {
  id: string
  user_id: string
  name: string
  description?: string
  status: string
  template_ids: string[]
  gmail_account_ids: string[]
  lead_ids: string[]
  schedule?: CampaignSchedule
  settings?: CampaignSettings
  total_leads: number
  sent_count: number
  open_count: number
  reply_count: number
  bounce_count: number
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface CampaignSchedule {
  start_date?: string
  end_date?: string
  send_time?: string
  timezone?: string
  send_interval_minutes?: number
  follow_up_delay_days?: number
  max_follow_ups?: number
  working_days_only?: boolean
}

export interface CampaignSettings {
  daily_send_limit?: number
  track_opens?: boolean
  track_clicks?: boolean
  personalize_subject?: boolean
  randomize_send_times?: boolean
  stop_on_reply?: boolean
  bcc_address?: string
  reply_to_address?: string
}

export interface CampaignLead {
  id: string
  campaign_id: string
  lead_id: string
  status: string
  sent_at?: string
  opened_at?: string
  replied_at?: string
  bounced_at?: string
  error_message?: string
  lead?: Lead
}

export interface EmailMessage {
  id: string
  campaign_lead_id?: string
  gmail_account_id: string
  from_email: string
  to_email: string
  subject: string
  body: string
  thread_id?: string
  message_id?: string
  in_reply_to?: string
  references?: string
  is_read: boolean
  is_reply: boolean
  labels: string[]
  received_at: string
  created_at: string
}

export interface EmailReply {
  id: string
  original_message_id: string
  from_email: string
  to_email: string
  subject: string
  body: string
  thread_id: string
  message_id: string
  received_at: string
  ai_summary?: string
  sentiment?: string
  intent?: string
  created_at: string
}

export interface Notification {
  id: string
  user_id: string
  type: string
  title: string
  message: string
  is_read: boolean
  data?: Record<string, any>
  created_at: string
}

export interface PipelineStage {
  id: string
  name: string
  order: number
  color?: string
  created_at: string
}

export interface WarmupProgress {
  id: string
  gmail_account_id: string
  date: string
  sent_count: number
  reply_count: number
  open_count: number
  spam_count: number
  score: number
  created_at: string
}

export interface SpamTest {
  id: string
  user_id: string
  subject: string
  body: string
  spam_score: number
  spam_status: string
  details: Record<string, any>
  created_at: string
}

export interface AnalyticsOverview {
  total_campaigns: number
  active_campaigns: number
  total_leads: number
  total_sent: number
  total_opens: number
  total_replies: number
  total_bounces: number
  open_rate: number
  reply_rate: number
  bounce_rate: number
  total_gmail_accounts: number
  active_gmail_accounts: number
  total_templates: number
}

export interface AnalyticsDaily {
  date: string
  sent: number
  opens: number
  replies: number
  bounces: number
}

export interface AnalyticsWeekly {
  week: string
  year: number
  week_number: number
  sent: number
  opens: number
  replies: number
  bounces: number
}

export interface AnalyticsMonthly {
  month: string
  year: number
  month_number: number
  sent: number
  opens: number
  replies: number
  bounces: number
}
