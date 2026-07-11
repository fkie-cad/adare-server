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

interface StatItemProps {
  icon: LucideIcon
  name: string
  count: number | undefined
}

function StatItem({ icon: Icon, name, count }: StatItemProps) {
  return (
    <div className="text-center px-4 py-2">
      <div className="font-mono text-xs uppercase tracking-widest text-muted-foreground">{name}</div>
      <Icon className="w-10 h-10 mx-auto my-2 text-primary/70" />
      <div className="font-mono text-3xl font-semibold tabular-nums text-primary">{count ?? '—'}</div>
    </div>
  )
}

export function WelcomeCard() {
  const { data: stats } = useStats()

  return (
    <Card className="shadow-lg">
      <CardHeader className="text-center">
        <h2 className="font-display text-5xl font-bold tracking-tight">
          Welcome to <span className="text-primary">ADARE</span>
        </h2>
        <p className="text-xl text-muted-foreground">
          The <b className="text-foreground">A</b>utomated <b className="text-foreground">D</b>esktop
          Forensic <b className="text-foreground">A</b>nalysis tool for{' '}
          <b className="text-foreground">R</b>eproducible <b className="text-foreground">E</b>xperiments
        </p>
      </CardHeader>
      <Separator />
      <CardContent className="flex justify-evenly flex-wrap py-6">
        <StatItem icon={PlayCircle} name="Runs" count={stats?.run_count} />
        <StatItem icon={FlaskConical} name="Experiments" count={stats?.experiment_count} />
        <StatItem icon={Boxes} name="Testfunctions" count={stats?.testfunction_count} />
        <StatItem icon={Users} name="Users" count={stats?.user_count} />
        <StatItem icon={GitPullRequest} name="Requests" count={stats?.request_count} />
      </CardContent>
      <Separator />
      <CardContent className="text-center py-4">
        <p className="text-lg">For access please write us a mail (mail@test.com)</p>
      </CardContent>
    </Card>
  )
}
