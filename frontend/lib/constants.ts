export const API_BASE_URL = "/api/v1"

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "LayoutDashboard" },
  { href: "/campaigns", label: "Campaigns", icon: "Send" },
  { href: "/leads", label: "Leads", icon: "Users" },
  { href: "/templates", label: "Templates", icon: "FileText" },
  { href: "/inbox", label: "Inbox", icon: "Inbox" },
  { href: "/replies", label: "Replies", icon: "Reply" },
  { href: "/analytics", label: "Analytics", icon: "BarChart3" },
  { href: "/spam-test", label: "Spam Test", icon: "ShieldAlert" },
  { href: "/warmup", label: "Warmup", icon: "Thermometer" },
  { href: "/gmail-accounts", label: "Gmail Accounts", icon: "Mail" },
  { href: "/settings", label: "Settings", icon: "Settings" },
]

export const PIPELINE_STAGES = ["Sent", "Opened", "Replied", "Interested", "Meeting", "Closed", "Not Interested"]

export const CAMPAIGN_STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-500",
  running: "bg-green-500",
  paused: "bg-yellow-500",
  completed: "bg-blue-500",
  failed: "bg-red-500",
}

export const LEAD_VALIDATION_COLORS: Record<string, string> = {
  pending: "bg-gray-500",
  valid: "bg-green-500",
  invalid: "bg-red-500",
  unknown: "bg-yellow-500",
}
