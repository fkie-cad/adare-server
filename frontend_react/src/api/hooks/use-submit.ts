import { useMutation } from '@tanstack/react-query'
import { api } from '@/api/client'
import { endpoints } from '@/api/endpoints'

interface SubmitResult {
  pr_url: string
  pr_number: number
}

export function useSubmitExperiment() {
  return useMutation({
    mutationFn: async ({
      name,
      playbook,
      metadata,
      description,
    }: {
      name: string
      playbook: File
      metadata: File
      description?: string
    }) => {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('playbook', playbook)
      formData.append('metadata', metadata)
      if (description) formData.append('description', description)
      const { data } = await api.post<SubmitResult>(endpoints.submitExperiment, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
  })
}

export function useSubmitTestfunction() {
  return useMutation({
    mutationFn: async ({
      name,
      testfunction,
      requirements,
      description,
    }: {
      name: string
      testfunction: File
      requirements: File
      description?: string
    }) => {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('testfunction', testfunction)
      formData.append('requirements', requirements)
      if (description) formData.append('description', description)
      const { data } = await api.post<SubmitResult>(endpoints.submitTestfunction, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
  })
}

export function useSubmitEnvironment() {
  return useMutation({
    mutationFn: async ({
      name,
      environment,
      description,
    }: {
      name: string
      environment: File
      description?: string
    }) => {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('environment', environment)
      if (description) formData.append('description', description)
      const { data } = await api.post<SubmitResult>(endpoints.submitEnvironment, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
  })
}
