import { useStats } from '@/api/hooks/use-stats'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import {
  PlayCircle,
  FlaskConical,
  Boxes,
  Users,
  GitPullRequest,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { entityAccents } from '@/constants/brand-accents'
import type { BrandAccent } from '@/constants/brand-accents'

interface StatItemProps {
  icon: LucideIcon
  name: string
  count: number | undefined
  accent: BrandAccent
}

function StatItem({ icon: Icon, name, count, accent }: StatItemProps) {
  return (
    <div className="text-center px-4 py-2">
      <div className="font-mono text-xs uppercase tracking-widest text-muted-foreground">{name}</div>
      <Icon className={`w-10 h-10 mx-auto my-2 ${accent.icon}`} />
      <div className={`font-mono text-3xl font-semibold tabular-nums ${accent.text}`}>{count ?? '—'}</div>
    </div>
  )
}

export function WelcomeCard() {
  const { data: stats } = useStats()

  return (
    <Card className="shadow-lg">
      <CardHeader className="text-center">
        <img src="/logo.svg" alt="ADARE" className="mx-auto h-44 w-44" />
        <p className="text-xl text-muted-foreground">
          The <b className="text-foreground">A</b>utomated <b className="text-foreground">D</b>esktop
          Forensic <b className="text-foreground">A</b>nalysis tool for{' '}
          <b className="text-foreground">R</b>eproducible <b className="text-foreground">E</b>xperiments
        </p>
      </CardHeader>
      <Separator />
      <CardContent className="flex justify-evenly flex-wrap py-6">
        <StatItem icon={PlayCircle} name="Runs" count={stats?.run_count} accent={entityAccents.run} />
        <StatItem icon={FlaskConical} name="Experiments" count={stats?.experiment_count} accent={entityAccents.experiment} />
        <StatItem icon={Boxes} name="Testfunctions" count={stats?.testfunction_count} accent={entityAccents.testfunctionset} />
        <StatItem icon={Users} name="Users" count={stats?.user_count} accent={entityAccents.user} />
        <StatItem icon={GitPullRequest} name="Requests" count={stats?.request_count} accent={entityAccents.request} />
      </CardContent>
      <Separator />
      <CardContent className="text-center py-4">
        <p className="text-lg">For access please write us a mail (mail@test.com)</p>
      </CardContent>
    </Card>
  )
}
