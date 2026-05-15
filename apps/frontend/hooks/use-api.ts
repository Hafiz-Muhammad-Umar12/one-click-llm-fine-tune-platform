"use client"

import axios from 'axios';
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"

// --- Datasets ---
export function useDatasets() {
  return useQuery({
    queryKey: ["datasets"],
    queryFn: async () => {
      const { data } = await api.get("/datasets/")
      return data
    },
  })
}

export function useUploadDataset() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, name }: { file: File, name: string }) => {
      // 1. Create dataset record
      const { data: dataset } = await api.post("/datasets/", { name, description: "" })
      
      // 2. Get presigned URL
      const { data: uploadParams } = await api.post(`/datasets/${dataset.id}/upload`)
      
      // 3. Upload to S3 directly via PUT
      await axios.put(uploadParams.upload_url, file, {
          headers: { 'Content-Type': file.type || 'application/octet-stream' }
      })
      
      // 4. Start processing
      await api.post(`/datasets/${dataset.id}/process`, { file_path: uploadParams.file_path })
      
      return dataset
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] })
    },
  })
}

// --- Training Jobs ---
export function useTrainingRuns() {
  return useQuery({
    queryKey: ["training-runs"],
    queryFn: async () => {
      const { data } = await api.get("/training/")
      return data
    },
  })
}

export function useCreateTrainingRun() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (runData: any) => {
      const { data } = await api.post("/training/", runData)
      await api.post(`/training/${data.id}/launch`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["training-runs"] })
    },
  })
}

// --- Deployments ---
export function useDeployments() {
  return useQuery({
    queryKey: ["deployments"],
    queryFn: async () => {
      const { data } = await api.get("/deployments/")
      return data
    },
  })
}

export function useCreateDeployment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (deploymentData: any) => {
      const { data } = await api.post("/deployments/", deploymentData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] })
    },
  })
}
