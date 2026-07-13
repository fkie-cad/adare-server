import { useParams } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { useExperiment } from '@/api/hooks/use-experiments'
import SubmitExperimentPage from '@/pages/submit-experiment'
import type { CurrentFile } from '@/pages/submit-shared'

export default function EditExperimentPage() {
  const { name } = useParams({ strict: false }) as { name: string }
  const { data: experiment, isLoading } = useExperiment(name)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  const currentFiles: CurrentFile[] = experiment
    ? [
        { label: 'playbook.yml', url: experiment.playbook_file },
        { label: 'metadata.yml', url: experiment.metadata_file },
      ]
    : []

  return <SubmitExperimentPage mode="edit" name={name} currentFiles={currentFiles} />
}
