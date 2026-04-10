import type { Profile } from '@/types/experiment'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ProfileImage } from './profile-image'
import { cn } from '@/lib/utils'

interface ProfileCardProps {
  profile: Profile
}

const roleColorMapping: Record<string, string> = {
  Owners: 'bg-foreground text-background border-border',
  Supervisor: 'bg-pink-700 text-white border-pink-600',
  admin: 'bg-foreground text-background border-border',
  supervisor: 'bg-pink-700 text-white border-pink-600',
}

function getRoleColor(role: string): string {
  return roleColorMapping[role] ?? 'bg-amber-400 text-foreground border-amber-300'
}

export function ProfileCard({ profile }: ProfileCardProps) {
  return (
    <Card className="max-w-lg mx-auto">
      <div className="bg-primary/15 h-32 flex items-end justify-center pb-0 relative">
        <div className="absolute -bottom-10">
          <ProfileImage profile={profile} size="lg" />
        </div>
      </div>
      <CardContent className="pt-14 space-y-2">
        <div className="flex justify-between p-2">
          <span className="text-lg text-muted-foreground">username</span>
          <span className="text-lg font-semibold">{profile.user.username}</span>
        </div>
        <Separator />
        <div className="flex justify-between p-2">
          <span className="text-lg text-muted-foreground">email</span>
          <span className="text-lg">{profile.user.email}</span>
        </div>
        <Separator />
        <div className="flex justify-between p-2">
          <span className="text-lg text-muted-foreground">teams</span>
          <div className="flex flex-wrap gap-1">
            {profile.teams.map((team) => (
              <span
                key={team.id}
                className={cn(
                  'rounded px-2 py-1 text-sm font-bold border-2',
                  getRoleColor(team.name),
                )}
              >
                {team.name}
              </span>
            ))}
          </div>
        </div>
        <Separator />
        <div className="p-2">
          <span className="text-lg text-muted-foreground">achievements</span>
        </div>
      </CardContent>
    </Card>
  )
}
