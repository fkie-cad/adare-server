import { useParams } from '@tanstack/react-router'
import { ExperimentOverview } from '@/components/experiment/experiment-overview'

export default function ExperimentDetailPage() {
  const { name } = useParams({ strict: false }) as { name: string }
  return <ExperimentOverview name={name} />
}
