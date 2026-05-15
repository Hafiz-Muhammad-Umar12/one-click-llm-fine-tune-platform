"use client"

import { useState } from "react"
import { Database, Plus, Upload, FileText, CheckCircle, Clock, AlertCircle, Trash2, Loader2 } from "lucide-react"
import { useDatasets, useUploadDataset } from "@/hooks/use-api"

export default function DatasetsPage() {
  const [isUploading, setIsUploading] = useState(false)
  const { data: datasets, isLoading } = useDatasets()
  const uploadMutation = useUploadDataset()

  const handleUpload = async (e: any) => {
      const file = e.target.files[0]
      if (!file) return
      
      try {
          await uploadMutation.mutateAsync({ file, name: file.name })
          setIsUploading(false)
      } catch (err) {
          console.error("Upload failed", err)
      }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-bold tracking-tight">Datasets</h2>
          <p className="text-muted-foreground">
            Manage your fine-tuning datasets and monitor processing.
          </p>
        </div>
        <button 
          onClick={() => setIsUploading(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus size={18} /> Upload Dataset
        </button>
      </div>

      {isUploading && (
        <div className="rounded-xl border border-dashed border-primary/50 bg-primary/5 p-12 text-center space-y-4">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
            {uploadMutation.isPending ? <Loader2 className="animate-spin" /> : <Upload size={24} />}
          </div>
          <div>
            <h3 className="font-semibold text-lg">Upload Dataset</h3>
            <p className="text-sm text-muted-foreground">Select a JSONL or CSV file to start processing</p>
          </div>
          <div className="flex justify-center gap-4">
            <label className="text-sm font-medium bg-primary text-primary-foreground px-4 py-2 rounded-md cursor-pointer">
                Select File
                <input type="file" className="hidden" onChange={handleUpload} disabled={uploadMutation.isPending} />
            </label>
            <button 
                onClick={() => setIsUploading(false)} 
                className="text-sm font-medium text-muted-foreground hover:text-foreground px-4 py-2"
                disabled={uploadMutation.isPending}
            >
                Cancel
            </button>
          </div>
        </div>
      )}

      {/* Dataset Table */}
      <div className="rounded-xl border bg-card overflow-hidden">
        {isLoading ? (
            <div className="p-12 text-center text-muted-foreground">Loading datasets...</div>
        ) : (
            <table className="w-full text-left">
            <thead className="bg-muted/50 border-b text-sm font-medium text-muted-foreground">
                <tr>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Format</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4">Actions</th>
                </tr>
            </thead>
            <tbody className="divide-y text-sm">
                {datasets?.map((ds: any) => (
                <tr key={ds.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4 flex items-center gap-3">
                    <FileText className="text-muted-foreground" size={18} />
                    <span className="font-medium">{ds.name}</span>
                    </td>
                    <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                        {ds.status === "ready" ? (
                        <CheckCircle size={16} className="text-green-500" />
                        ) : (
                        <Clock size={16} className="text-amber-500 animate-spin-slow" />
                        )}
                        <span className="capitalize">{ds.status}</span>
                    </div>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground uppercase">
                    {ds.format || "N/A"}
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">{new Date(ds.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4">
                    <button className="text-destructive hover:bg-destructive/10 p-2 rounded-md transition-colors">
                        <Trash2 size={16} />
                    </button>
                    </td>
                </tr>
                ))}
                {datasets?.length === 0 && (
                    <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">No datasets found. Upload one to get started.</td>
                    </tr>
                )}
            </tbody>
            </table>
        )}
      </div>
    </div>
  )
}
