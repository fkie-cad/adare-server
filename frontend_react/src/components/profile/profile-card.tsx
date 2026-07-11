import type { Profile } from '@/types/experiment'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Tooltip } from '@/components/ui/tooltip'
import { ProfileImage } from './profile-image'
import { cn } from '@/lib/utils'
import { API_BASE } from '@/api/endpoints'

interface ProfileCardProps {
  profile: Profile
}

const roleColorMapping: Record<string, string> = {
  Owners: 'bg-foreground text-background border-transparent',
  Supervisor: 'bg-primary text-primary-foreground border-transparent',
  admin: 'bg-foreground text-background border-transparent',
  supervisor: 'bg-primary text-primary-foreground border-transparent',
}

function getRoleColor(role: string): string {
  return roleColorMapping[role] ?? 'bg-muted text-foreground border-border'
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
          {profile.achievements.length === 0 ? (
            <p className="text-sm text-muted-foreground mt-2">No achievements yet</p>
          ) : (
            <div className="grid grid-cols-4 gap-3 mt-3">
              {profile.achievements.map((achievement) => (
                <Tooltip key={achievement.name} content={achievement.description}>
                  <div className="flex flex-col items-center gap-1 relative">
                    <img
                      src={`${API_BASE}file/achievements/${achievement.iconfile}`}
                      alt={achievement.name}
                      className="w-12 h-12"
                    />
                    {achievement.count > 1 && (
                      <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                        {achievement.count}
                      </span>
                    )}
                    <span className="text-xs text-center font-medium leading-tight">
                      {achievement.name}
                    </span>
                  </div>
                </Tooltip>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
