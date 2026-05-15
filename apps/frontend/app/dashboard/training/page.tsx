"use client"

import { useState } from "react"
import { Cpu, Plus, Play, Info, CheckCircle2, XCircle, Clock, ChevronRight, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTrainingRuns, useCreateTrainingRun, useDatasets } from "@/hooks/use-api"

export default function TrainingPage() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const { data: trainingRuns, isLoading } = useTrainingRuns()
  const { data: datasets } = useDatasets()
  const createMutation = useCreateTrainingRun()

  const [formData, setFormData] = useState({
      name: "",
      dataset_id: "",
      base_model: "meta-llama/Llama-3-8b",
      method: "lora",
      hardware_tier: "nvidia-l4-1x"
  })

  const handleLaunch = async () => {
      try {
          await createMutation.mutateAsync({
              name: formData.name,
              contract_id: formData.dataset_id, // Simplified for demo
              training_config: {
                  method: formData.method,
                  base_model: formData.base_model,
                  hardware_tier: formData.hardware_tier
              }
          })
          setShowCreateForm(false)
      } catch (err) {
          console.error("Launch failed", err)
      }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-bold tracking-tight">Training Jobs</h2>
          <p className="text-muted-foreground">
            Monitor and launch fine-tuning experiments.
          </p>
        </div>
        <button 
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus size={18} /> New Training Job
        </button>
      </div>

      {showCreateForm && (
        <div className="rounded-xl border bg-card p-8 space-y-6 shadow-md border-primary/20">
           <div className="flex items-center justify-between">
             <h3 className="text-xl font-bold">Configure Training Job</h3>
             <button onClick={() => setShowCreateForm(false)} className="text-muted-foreground hover:text-foreground">Cancel</button>
           </div>
           
           <div className="grid grid-cols-2 gap-6">
             <div className="space-y-2">
                <label className="text-sm font-medium">Job Name</label>
                <input 
                    type="text" 
                    placeholder="e.g. llama3-customer-v1"
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
             </div>
             <div className="space-y-2">
               <label className="text-sm font-medium">Dataset</label>
               <select 
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={formData.dataset_id}
                onChange={(e) => setFormData({...formData, dataset_id: e.target.value})}
               >
                 <option value="">Select a dataset</option>
                 {datasets?.map((ds: any) => (
                     <option key={ds.id} value={ds.id}>{ds.name}</option>
                 ))}
               </select>
             </div>
             <div className="space-y-2">
               <label className="text-sm font-medium">Base Model</label>
               <select 
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={formData.base_model}
                onChange={(e) => setFormData({...formData, base_model: e.target.value})}
               >
                 <option value="meta-llama/Meta-Llama-3-8B-Instruct">Meta-Llama-3-8B-Instruct</option>
                 <option value="mistralai/Mistral-7B-v0.1">Mistral-7B-v0.1</option>
               </select>
             </div>
             <div className="space-y-2">
               <label className="text-sm font-medium">Hardware Tier</label>
               <select 
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={formData.hardware_tier}
                onChange={(e) => setFormData({...formData, hardware_tier: e.target.value})}
               >
                 <option value="nvidia-l4-1x">NVIDIA L4 (24GB VRAM) - 1x</option>
                 <option value="nvidia-a100-40gb-1x">NVIDIA A100 (40GB VRAM) - 1x</option>
               </select>
             </div>
           </div>

           <div className="flex justify-end gap-4 border-t pt-6">
              <button 
                onClick={handleLaunch}
                disabled={createMutation.isPending || !formData.dataset_id}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play size={16} />} 
                Launch Job
              </button>
           </div>
        </div>
      )}

      {/* Jobs Table */}
      <div className="rounded-xl border bg-card overflow-hidden">
        {isLoading ? (
            <div className="p-12 text-center text-muted-foreground">Loading training runs...</div>
        ) : (
            <table className="w-full text-left">
            <thead className="bg-muted/50 border-b text-sm font-medium text-muted-foreground">
                <tr>
                <th className="px-6 py-4">Job Name</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Model</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4 text-right">Actions</th>
                </tr>
            </thead>
            <tbody className="divide-y text-sm">
                {trainingRuns?.map((job: any) => (
                <tr key={job.id} className="group hover:bg-muted/30 transition-colors cursor-pointer">
                    <td className="px-6 py-4">
                    <div className="font-medium">{job.name}</div>
                    <div className="text-xs text-muted-foreground truncate max-w-[200px]">{job.id}</div>
                    </td>
                    <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                        {job.status === "completed" && <CheckCircle2 size={16} className="text-green-500" />}
                        {job.status === "running" && <Clock size={16} className="text-primary animate-pulse" />}
                        {job.status === "pending" && <Clock size={16} className="text-muted-foreground" />}
                        {job.status === "failed" && <XCircle size={16} className="text-destructive" />}
                        <span className={cn(
                        "font-medium capitalize",
                        job.status === "completed" && "text-green-500",
                        job.status === "failed" && "text-destructive"
                        )}>{job.status}</span>
                    </div>
                    </td>
                    <td className="px-6 py-4">
                    <div className="text-muted-foreground">{job.training_config?.base_model || "Unknown"}</div>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">{new Date(job.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right">
                    <ChevronRight size={16} className="text-muted-foreground ml-auto group-hover:translate-x-1 transition-transform" />
                    </td>
                </tr>
                ))}
                {trainingRuns?.length === 0 && (
                    <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">No training jobs found.</td>
                    </tr>
                )}
            </tbody>
            </table>
        )}
      </div>
    </div>
  )
}
