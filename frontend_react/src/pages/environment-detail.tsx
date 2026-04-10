import { useParams } from '@tanstack/react-router'
import { EnvironmentOverview } from '@/components/environment/environment-overview'

export default function EnvironmentDetailPage() {
  const { name } = useParams({ strict: false }) as { name: string }
  return <EnvironmentOverview name={name} />
}
