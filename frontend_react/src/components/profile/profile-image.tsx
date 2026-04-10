import { Link } from '@tanstack/react-router'
import type { Profile } from '@/types/experiment'
import type { SizeType } from '@/constants'
import { sizePixelMapping, sizeFontMapping } from '@/constants'
import { Tooltip } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface ProfileImageProps {
  profile: Profile
  size?: SizeType
  showTooltip?: boolean
  linkToProfile?: boolean
}

export function ProfileImage({
  profile,
  size = 'md',
  showTooltip = false,
  linkToProfile = false,
}: ProfileImageProps) {
  const sizeClass = sizePixelMapping[size]
  const fontClass = sizeFontMapping[size]

  const avatar = profile.avatar ? (
    <img
      src={profile.avatar}
      alt={profile.user.username}
      className={cn('rounded-full object-cover', sizeClass)}
    />
  ) : (
    <div
      className={cn(
        'rounded-full bg-secondary flex items-center justify-center font-semibold text-white',
        sizeClass,
        fontClass,
      )}
    >
      {profile.user.username.charAt(0).toUpperCase()}
    </div>
  )

  let content = avatar

  if (showTooltip) {
    content = <Tooltip content={profile.user.username}>{content}</Tooltip>
  }

  if (linkToProfile) {
    return (
      <Link to="/user/$username" params={{ username: profile.user.username }}>
        {content}
      </Link>
    )
  }

  return content
}
