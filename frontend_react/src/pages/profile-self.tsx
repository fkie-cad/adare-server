import { Loader2 } from 'lucide-react'
import { useLoggedInUser } from '@/api/hooks/use-user'
import { ProfileCard } from '@/components/profile/profile-card'

export default function ProfileSelfPage() {
  const { data: profile, isLoading } = useLoggedInUser()

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (!profile) {
    return <p className="text-center py-12">Not logged in</p>
  }

  return <ProfileCard profile={profile} />
}
