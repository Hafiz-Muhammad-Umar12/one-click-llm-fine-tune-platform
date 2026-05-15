"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Database, 
  Cpu, 
  Rocket, 
  Settings, 
  LogOut,
  ChevronLeft,
  ChevronRight,
  User,
  Activity
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/use-auth-store"

const sidebarItems = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Datasets", href: "/dashboard/datasets", icon: Database },
  { name: "Training", href: "/dashboard/training", icon: Cpu },
  { name: "Deployments", href: "/dashboard/deployments", icon: Rocket },
  { name: "Observability", href: "/dashboard/observability", icon: Activity },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pathname = usePathname()
  const { user, logout } = useAuthStore()

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside 
        className={cn(
          "relative border-r bg-card transition-all duration-300",
          isCollapsed ? "w-16" : "w-64"
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b">
          {!isCollapsed && <span className="text-xl font-bold text-primary">One-Click AI</span>}
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="rounded-md p-1 hover:bg-muted"
          >
            {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
        </div>

        <nav className="space-y-1 p-2">
          {sidebarItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-primary text-primary-foreground" 
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <item.icon size={20} />
                {!isCollapsed && <span>{item.name}</span>}
              </Link>
            )
          })}
        </nav>

        <div className="absolute bottom-4 w-full px-2 space-y-1">
           <div className={cn(
             "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground",
             isCollapsed ? "justify-center" : ""
           )}>
             <User size={20} />
             {!isCollapsed && <span className="truncate">{user?.email || "User"}</span>}
           </div>
           <button
            onClick={logout}
            className={cn(
              "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-destructive transition-colors hover:bg-destructive/10",
              isCollapsed ? "justify-center" : ""
            )}
          >
            <LogOut size={20} />
            {!isCollapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <header className="flex h-16 items-center justify-between border-b px-8 bg-card">
          <h1 className="text-lg font-semibold">
            {sidebarItems.find(i => i.href === pathname)?.name || "Dashboard"}
          </h1>
          <div className="flex items-center gap-4">
             {/* Additional Header Actions (Notifications, etc) */}
          </div>
        </header>
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
