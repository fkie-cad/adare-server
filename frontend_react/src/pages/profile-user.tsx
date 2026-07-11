import { useParams } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { useUserProfile } from '@/api/hooks/use-user'
import { ProfileCard } from '@/components/profile/profile-card'
import { PageContainer } from '@/components/layout/page-container'

export default function ProfileUserPage() {
  const { username } = useParams({ strict: false }) as { username: string }
  const { data: profile, isLoading } = useUserProfile(username)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (!profile) {
    return <p className="text-center py-12">User not found</p>
  }

  return (
    <PageContainer>
      <ProfileCard profile={profile} />
    </PageContainer>
  )
}
