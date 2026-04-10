import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <h1 className="text-6xl font-bold text-muted-foreground">404</h1>
      <p className="text-xl mt-4 mb-8">Page not found</p>
      <Button asChild>
        <Link to="/home">Go Home</Link>
      </Button>
    </div>
  )
}
