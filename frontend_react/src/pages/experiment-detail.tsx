import { useParams } from '@tanstack/react-router'
import { ExperimentOverview } from '@/components/experiment/experiment-overview'
import { PageContainer } from '@/components/layout/page-container'

export default function ExperimentDetailPage() {
  const { name } = useParams({ strict: false }) as { name: string }
  return (
    <PageContainer className="max-w-4xl">
      <ExperimentOverview name={name} />
    </PageContainer>
  )
}
