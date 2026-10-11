import { api } from '@/api/client'

export async function downloadFile(url: string, filename?: string) {
  const response = await api.get(url, { responseType: 'blob' })
  const blob = new Blob([response.data])
  const name = filename ?? url.split('/').pop()?.split('?')[0] ?? 'download'
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = name
  link.click()
  URL.revokeObjectURL(link.href)
}
