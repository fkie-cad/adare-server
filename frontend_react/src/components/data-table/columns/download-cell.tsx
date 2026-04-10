import { Download } from 'lucide-react'
import { api } from '@/api/client'
import { Button } from '@/components/ui/button'

interface DownloadCellProps {
  url: string | null | undefined
}

export function DownloadCell({ url }: DownloadCellProps) {
  if (!url) return null

  const filename = url.split('/').pop()?.split('?')[0] ?? 'download'

  const handleDownload = async () => {
    const response = await api.get(url, { responseType: 'blob' })
    const blob = new Blob([response.data])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
    URL.revokeObjectURL(link.href)
  }

  return (
    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleDownload}>
      <Download className="h-4 w-4" />
    </Button>
  )
}
