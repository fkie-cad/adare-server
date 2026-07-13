import { useMutation } from '@tanstack/react-query'
import { api } from '@/api/client'
import { endpoints } from '@/api/endpoints'

interface SubmitResult {
  pr_url: string
  pr_number: number
}

export type SubmitAction = 'create' | 'modify' | 'remove'

async function postForm(endpoint: string, formData: FormData): Promise<SubmitResult> {
  const { data } = await api.post<SubmitResult>(endpoint, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export function useSubmitExperiment() {
  return useMutation({
    mutationFn: async ({
      name,
      playbook,
      metadata,
      description,
      action = 'create',
    }: {
      name: string
      playbook?: File
      metadata?: File
      description?: string
      action?: SubmitAction
    }) => {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('action', action)
      if (playbook) formData.append('playbook', playbook)
      if (metadata) formData.append('metadata', metadata)
      if (description) formData.append('description', description)
      return postForm(endpoints.submitExperiment, formData)
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
      action = 'create',
    }: {
      name: string
      testfunction?: File
      requirements?: File
      description?: string
      action?: SubmitAction
    }) => {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('action', action)
      if (testfunction) formData.append('testfunction', testfunction)
      if (requirements) formData.append('requirements', requirements)
      if (description) formData.append('description', description)
      return postForm(endpoints.submitTestfunction, formData)
    },
  })
}

export function useSubmitEnvironment() {
  return useMutation({
    mutationFn: async ({
      name,
      environment,
      description,
      action = 'create',
    }: {
      name: string
      environment?: File
      description?: string
      action?: SubmitAction
    }) => {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('action', action)
      if (environment) formData.append('environment', environment)
      if (description) formData.append('description', description)
      return postForm(endpoints.submitEnvironment, formData)
    },
  })
}
