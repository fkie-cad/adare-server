import { useParams } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { useEnvironment } from '@/api/hooks/use-environments'
import SubmitEnvironmentPage from '@/pages/submit-environment'
import type { CurrentFile } from '@/pages/submit-shared'

export default function EditEnvironmentPage() {
  const { name } = useParams({ strict: false }) as { name: string }
  const { data: environment, isLoading } = useEnvironment(name)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  const currentFiles: CurrentFile[] = environment
    ? [{ label: `${name}.yml`, url: environment.file }]
    : []

  return <SubmitEnvironmentPage mode="edit" name={name} currentFiles={currentFiles} />
}
