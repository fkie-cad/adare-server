import { useUserProfile } from '@/api/hooks/use-user'
import { ProfileImage } from '@/components/profile/profile-image'

interface UserIconCellProps {
  username: string
}

export function UserIconCell({ username }: UserIconCellProps) {
  const { data: profile } = useUserProfile(username)

  if (!profile) return <span className="text-sm text-muted-foreground">{username}</span>

  return <ProfileImage profile={profile} size="sm" showTooltip linkToProfile />
}
