"use client"

import { Settings, Shield, CreditCard, Users, Bell, Globe } from "lucide-react"

const sections = [
  { name: "General", icon: Settings, desc: "Manage your organization profile and basic settings." },
  { name: "Team", icon: Users, desc: "Invite members and manage permissions." },
  { name: "Security", icon: Shield, desc: "API Keys, Two-factor authentication, and Audit logs." },
  { name: "Billing", icon: CreditCard, desc: "Manage your subscription, usage quotas, and invoices." },
  { name: "Notifications", icon: Bell, desc: "Configure email and webhook alerts for job completions." },
  { name: "API & Integration", icon: Globe, desc: "Endpoints and documentation for external access." },
]

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">
          Configure your workspace and enterprise features.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {sections.map((section) => (
          <div key={section.name} className="flex gap-4 rounded-xl border bg-card p-6 shadow-sm hover:bg-muted/30 transition-colors cursor-pointer group">
             <div className="p-3 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors h-fit">
               <section.icon size={24} />
             </div>
             <div className="space-y-1">
               <h3 className="font-bold">{section.name}</h3>
               <p className="text-sm text-muted-foreground">{section.desc}</p>
             </div>
          </div>
        ))}
      </div>
    </div>
  )
}
