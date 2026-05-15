"use client"

import { useState } from "react"
import { Rocket, Plus, Activity, Zap, ExternalLink, Shield, Server, ArrowRight, Loader2, CheckCircle2, Clock } from "lucide-react"
import { cn } from "@/lib/utils"
import { useDeployments, useCreateDeployment, useTrainingRuns } from "@/hooks/use-api"

export default function DeploymentsPage() {
  const [showDeployForm, setShowDeployForm] = useState(false)
  const { data: deployments, isLoading } = useDeployments()
  const { data: trainingRuns } = useTrainingRuns()
  const createMutation = useCreateDeployment()

  const [formData, setFormData] = useState({
      name: "",
      model_version_id: "",
      hardware_tier: "nvidia-l4-1x",
      min_replicas: 1,
      max_replicas: 3
  })

  const handleDeploy = async () => {
      try {
          await createMutation.mutateAsync({
              name: formData.name,
              model_version_id: formData.model_version_id,
              hardware_tier: formData.hardware_tier,
              target_replica_count: formData.min_replicas,
              autoscaling_config: {
                  min_replicas: formData.min_replicas,
                  max_replicas: formData.max_replicas
              }
          })
          setShowDeployForm(false)
      } catch (err) {
          console.error("Deployment failed", err)
      }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-bold tracking-tight">Deployments</h2>
          <p className="text-muted-foreground">
            Manage your inference endpoints and monitor real-time performance.
          </p>
        </div>
        <button 
          onClick={() => setShowDeployForm(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus size={18} /> New Deployment
        </button>
      </div>

      {showDeployForm && (
        <div className="rounded-xl border bg-card p-8 space-y-6 shadow-md border-primary/20">
           <div className="flex items-center justify-between">
             <h3 className="text-xl font-bold">Deploy Inference Endpoint</h3>
             <button onClick={() => setShowDeployForm(false)} className="text-muted-foreground hover:text-foreground">Cancel</button>
           </div>
           
           <div className="grid grid-cols-2 gap-6">
             <div className="space-y-2">
                <label className="text-sm font-medium">Endpoint Name</label>
                <input 
                    type="text" 
                    placeholder="e.g. customer-service-prod"
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
             </div>
             <div className="space-y-2">
               <label className="text-sm font-medium">Model Version (Training Run)</label>
               <select 
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={formData.model_version_id}
                onChange={(e) => setFormData({...formData, model_version_id: e.target.value})}
               >
                 <option value="">Select a completed run</option>
                 {trainingRuns?.filter((r: any) => r.status === "completed").map((run: any) => (
                     <option key={run.id} value={run.id}>{run.name} ({run.training_config.base_model})</option>
                 ))}
                 {/* For demo, show all if none completed */}
                 {trainingRuns?.length > 0 && trainingRuns.filter((r: any) => r.status === "completed").length === 0 && (
                     trainingRuns.map((run: any) => (
                        <option key={run.id} value={run.id}>{run.name} (Force Select)</option>
                     ))
                 )}
               </select>
             </div>
             <div className="space-y-2">
               <label className="text-sm font-medium">Hardware Tier</label>
               <select 
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={formData.hardware_tier}
                onChange={(e) => setFormData({...formData, hardware_tier: e.target.value})}
               >
                 <option value="nvidia-l4-1x">NVIDIA L4 (24GB) - $0.60/hr</option>
                 <option value="nvidia-a100-40gb-1x">NVIDIA A100 (40GB) - $1.80/hr</option>
               </select>
             </div>
             <div className="space-y-2">
               <label className="text-sm font-medium">Replicas (Min/Max)</label>
               <div className="flex gap-4">
                 <input 
                    type="number" 
                    className="w-20 h-10 rounded-md border border-input bg-background px-3 text-sm" 
                    value={formData.min_replicas}
                    onChange={(e) => setFormData({...formData, min_replicas: parseInt(e.target.value)})}
                 />
                 <span className="self-center">/</span>
                 <input 
                    type="number" 
                    className="w-20 h-10 rounded-md border border-input bg-background px-3 text-sm" 
                    value={formData.max_replicas}
                    onChange={(e) => setFormData({...formData, max_replicas: parseInt(e.target.value)})}
                 />
               </div>
             </div>
           </div>

           <div className="flex justify-end gap-4 border-t pt-6">
              <button 
                onClick={handleDeploy}
                disabled={createMutation.isPending || !formData.model_version_id}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket size={16} />} 
                Deploy Endpoint
              </button>
           </div>
        </div>
      )}

      {/* Deployment Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
            <div className="col-span-full p-12 text-center text-muted-foreground">Loading deployments...</div>
        ) : deployments?.map((dep: any) => (
          <div key={dep.id} className="rounded-xl border bg-card p-6 shadow-sm hover:shadow-md transition-shadow group relative">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Zap size={20} />
              </div>
              <div className={cn(
                "px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1",
                dep.status === "active" ? "bg-green-500/10 text-green-500" : "bg-amber-500/10 text-amber-500"
              )}>
                {dep.status === "active" ? <CheckCircle2 size={10} /> : <Clock size={10} />}
                {dep.status}
              </div>
            </div>

            <div className="space-y-1 mb-6">
              <h3 className="font-bold text-lg">{dep.name}</h3>
              <p className="text-xs text-muted-foreground truncate">{dep.id}</p>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6 text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <Server size={14} /> {dep.hardware_tier}
              </div>
              <div className="flex items-center gap-2">
                <Activity size={14} /> {dep.target_replica_count} Replicas
              </div>
            </div>

            <div className="flex gap-2">
               <button className="flex-1 inline-flex items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90">
                 Playground <ArrowRight size={14} />
               </button>
               <button className="p-2 rounded-md border hover:bg-muted text-muted-foreground">
                 <Settings size={14} />
               </button>
            </div>
          </div>
        ))}
        {deployments?.length === 0 && !isLoading && (
            <div className="col-span-full p-12 text-center border-2 border-dashed rounded-xl text-muted-foreground">
                No active deployments. Select a model to deploy.
            </div>
        )}
      </div>
    </div>
  )
}
