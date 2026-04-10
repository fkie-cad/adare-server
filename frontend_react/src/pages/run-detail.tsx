import { useParams } from '@tanstack/react-router'
import { RunDetailView } from '@/components/run/run-detail'

export default function RunDetailPage() {
  const { ulid } = useParams({ strict: false }) as { ulid: string }
  return <RunDetailView ulid={ulid} />
}
