"use client"

import { Activity, TrendingUp, BarChart3, Timer, AlertTriangle, ShieldCheck } from "lucide-react"

export default function ObservabilityPage() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Observability</h2>
        <p className="text-muted-foreground">
          Real-time system health, GPU metrics, and inference telemetry.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
         <div className="rounded-xl border bg-card p-6 space-y-4">
            <div className="flex items-center gap-2 text-primary font-semibold">
              <Timer className="h-5 w-5" /> API Latency (P99)
            </div>
            <div className="text-3xl font-bold">142ms</div>
            <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
               <div className="bg-primary h-full w-[65%]" />
            </div>
         </div>
         <div className="rounded-xl border bg-card p-6 space-y-4">
            <div className="flex items-center gap-2 text-green-500 font-semibold">
              <ShieldCheck className="h-5 w-5" /> System Uptime
            </div>
            <div className="text-3xl font-bold">99.98%</div>
            <div className="text-xs text-muted-foreground">Last 30 days</div>
         </div>
         <div className="rounded-xl border bg-card p-6 space-y-4">
            <div className="flex items-center gap-2 text-amber-500 font-semibold">
              <AlertTriangle className="h-5 w-5" /> Active Alerts
            </div>
            <div className="text-3xl font-bold">0</div>
            <div className="text-xs text-muted-foreground">All systems operational</div>
         </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
         <div className="rounded-xl border bg-card p-6 h-80 flex flex-col">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> GPU Utilization (Aggregate)
            </h3>
            <div className="flex-1 flex items-center justify-center border-2 border-dashed rounded-lg bg-muted/20">
               <span className="text-muted-foreground text-sm italic">Prometheus/Grafana chart will be embedded here</span>
            </div>
         </div>
         <div className="rounded-xl border bg-card p-6 h-80 flex flex-col">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" /> Inference Token Throughput
            </h3>
            <div className="flex-1 flex items-center justify-center border-2 border-dashed rounded-lg bg-muted/20">
               <span className="text-muted-foreground text-sm italic">OpenTelemetry traces will be visualized here</span>
            </div>
         </div>
      </div>
    </div>
  )
}
