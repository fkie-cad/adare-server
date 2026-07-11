import { useParams } from '@tanstack/react-router'
import { RunDetailView } from '@/components/run/run-detail'
import { PageContainer } from '@/components/layout/page-container'

export default function RunDetailPage() {
  const { ulid } = useParams({ strict: false }) as { ulid: string }
  return (
    <PageContainer className="max-w-4xl">
      <RunDetailView ulid={ulid} />
    </PageContainer>
  )
}
