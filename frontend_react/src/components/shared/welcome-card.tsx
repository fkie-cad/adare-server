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
  colorClass: string
}

function StatItem({ icon: Icon, name, count, colorClass }: StatItemProps) {
  return (
    <div className="text-center px-4 py-2">
      <div className={`text-lg font-semibold ${colorClass}`}>{name}</div>
      <Icon className={`w-12 h-12 mx-auto my-2 ${colorClass}`} />
      <div className={`text-3xl font-bold ${colorClass}`}>{count ?? '-'}</div>
    </div>
  )
}

export function WelcomeCard() {
  const { data: stats } = useStats()

  return (
    <Card>
      <CardHeader className="text-center">
        <h2 className="text-4xl font-bold">Welcome to ADARE</h2>
        <p className="text-lg">
          The <b>A</b>utomated <b>D</b>esktop Forensic <b>A</b>nalysis tool for{' '}
          <b>R</b>eproducible <b>E</b>xperiments
        </p>
      </CardHeader>
      <Separator />
      <CardContent className="flex justify-evenly flex-wrap py-6">
        <StatItem icon={PlayCircle} name="Runs" count={stats?.run_count} colorClass="text-indigo-500" />
        <StatItem icon={FlaskConical} name="Experiments" count={stats?.experiment_count} colorClass="text-teal-600" />
        <StatItem icon={Boxes} name="Testfunctions" count={stats?.testfunction_count} colorClass="text-purple-500" />
        <StatItem icon={Users} name="Users" count={stats?.user_count} colorClass="text-red-500" />
        <StatItem icon={GitPullRequest} name="Requests" count={stats?.request_count} colorClass="text-orange-500" />
      </CardContent>
      <Separator />
      <CardContent className="text-center py-4">
        <p className="text-lg">For access please write us a mail (mail@test.com)</p>
      </CardContent>
    </Card>
  )
}
