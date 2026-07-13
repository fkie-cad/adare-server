import { useParams } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { useTestfunctionSet } from '@/api/hooks/use-testfunction-sets'
import SubmitTestfunctionPage from '@/pages/submit-testfunction'
import type { CurrentFile } from '@/pages/submit-shared'

export default function EditTestfunctionPage() {
  const { name } = useParams({ strict: false }) as { name: string }
  const { data: tfSet, isLoading } = useTestfunctionSet(name)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  const currentFiles: CurrentFile[] = tfSet
    ? [
        { label: `${name}.py`, url: tfSet.file },
        { label: 'requirements.txt', url: tfSet.requirements_file },
      ]
    : []

  return <SubmitTestfunctionPage mode="edit" name={name} currentFiles={currentFiles} />
}
