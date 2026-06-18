"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Send,
  Users,
  FileText,
  Inbox,
  ReplyAll,
  BarChart3,
  ShieldAlert,
  Thermometer,
  Mail,
  Settings,
  Sun,
  Moon,
  LogOut,
} from "lucide-react"
import { useTheme } from "next-themes"
import { NAV_ITEMS } from "@/lib/constants"
import { useAuthContext } from "@/providers/auth-provider"
import { useAuth } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetClose } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  LayoutDashboard,
  Send,
  Users,
  FileText,
  Inbox,
  Reply: ReplyAll,
  BarChart3,
  ShieldAlert,
  Thermometer,
  Mail,
  Settings,
}

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

function SidebarContent({ onClose }: { onClose?: () => void }) {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const { user } = useAuthContext()
  const { logout } = useAuth()

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center border-b px-6">
        <Link href="/dashboard" className="flex items-center gap-2 font-semibold" onClick={onClose}>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
            O
          </div>
          <span className="text-lg">Outreach CRM</span>
        </Link>
      </div>
      <ScrollArea className="flex-1 px-3 py-2">
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const Icon = iconMap[item.icon]
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                {Icon && <Icon className="h-4 w-4" />}
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </ScrollArea>
      <Separator />
      <div className="p-3">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="text-xs">
              {user?.name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || "U"}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-medium leading-none truncate">{user?.name || "User"}</p>
            <p className="text-xs text-muted-foreground truncate mt-0.5">{user?.email || ""}</p>
          </div>
        </div>
        <div className="mt-2 flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9 ml-auto" onClick={logout}>
            <LogOut className="h-4 w-4" />
            <span className="sr-only">Logout</span>
          </Button>
        </div>
      </div>
    </div>
  )
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent side="left" className="p-0 w-72">
          <SheetClose />
          <SidebarContent onClose={onClose} />
        </SheetContent>
      </Sheet>
      <aside className="hidden lg:flex lg:w-72 lg:flex-col lg:border-r">
        <SidebarContent />
      </aside>
    </>
  )
}
