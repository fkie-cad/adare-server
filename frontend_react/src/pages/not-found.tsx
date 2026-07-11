import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-20">
      <h1 className="font-mono text-6xl font-bold tabular-nums text-primary">404</h1>
      <p className="mt-4 mb-8 text-xl">Page not found</p>
      <Button asChild>
        <Link to="/home">Go Home</Link>
      </Button>
    </div>
  )
}
