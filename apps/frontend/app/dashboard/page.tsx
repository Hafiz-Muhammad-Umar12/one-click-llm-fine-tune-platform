"use client"

import { Database, Cpu, Rocket, Activity, ArrowUpRight, TrendingUp } from "lucide-react"

const stats = [
  { name: "Total Datasets", value: "12", change: "+2", icon: Database },
  { name: "Training Jobs", value: "4", change: "Running", icon: Cpu },
  { name: "Active Endpoints", value: "8", change: "Healthy", icon: Rocket },
  { name: "Total Inference", value: "1.2M", change: "+12%", icon: Activity },
]

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">System Overview</h2>
        <p className="text-muted-foreground">
          Monitor your AI infrastructure performance and job status.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="rounded-xl border bg-card p-6 shadow-sm">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <span className="text-sm font-medium">{stat.name}</span>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="flex items-baseline justify-between mt-2">
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="flex items-center text-xs font-medium text-primary">
                {stat.change}
                <ArrowUpRight className="ml-1 h-3 w-3" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity Mockup */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="col-span-4 rounded-xl border bg-card p-6 shadow-sm">
           <h3 className="font-semibold mb-4 flex items-center gap-2">
             <TrendingUp className="h-4 w-4" /> Training Throughput (Tokens/sec)
           </h3>
           <div className="h-[200px] flex items-center justify-center border-2 border-dashed rounded-lg bg-muted/30">
             <span className="text-muted-foreground text-sm">Throughput visualization will render here</span>
           </div>
        </div>

        <div className="col-span-3 rounded-xl border bg-card p-6 shadow-sm">
          <h3 className="font-semibold mb-4">Recent Training Jobs</h3>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <div>
                    <div className="font-medium">job-llama3-fine-tune-{i}</div>
                    <div className="text-xs text-muted-foreground text-opacity-70">Llama-3-8B • LoRA</div>
                  </div>
                </div>
                <div className="text-muted-foreground">2h ago</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
