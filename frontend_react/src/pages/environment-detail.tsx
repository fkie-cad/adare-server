import { useParams } from '@tanstack/react-router'
import { EnvironmentOverview } from '@/components/environment/environment-overview'
import { PageContainer } from '@/components/layout/page-container'

export default function EnvironmentDetailPage() {
  const { name } = useParams({ strict: false }) as { name: string }
  return (
    <PageContainer className="max-w-4xl">
      <EnvironmentOverview name={name} />
    </PageContainer>
  )
}
