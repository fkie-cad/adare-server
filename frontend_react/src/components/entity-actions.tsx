import { useState } from 'react'
import { Link } from '@tanstack/react-router'
import { Pencil, Trash2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  useSubmitExperiment,
  useSubmitEnvironment,
  useSubmitTestfunction,
} from '@/api/hooks/use-submit'
import { extractSubmitError } from '@/pages/submit-shared'
import { useAuthStore } from '@/stores/auth-store'

type EntityType = 'experiment' | 'environment' | 'testfunction'

interface EntityActionsProps {
  entity: EntityType
  name: string
  /** Route to the edit form, e.g. `/experiment/$name/edit`. */
  editTo: string
}

const LABELS: Record<EntityType, string> = {
  experiment: 'experiment',
  environment: 'environment',
  testfunction: 'testfunction',
}

export function EntityActions({ entity, name, editTo }: EntityActionsProps) {
  const [confirming, setConfirming] = useState(false)

  const experimentMut = useSubmitExperiment()
  const environmentMut = useSubmitEnvironment()
  const testfunctionMut = useSubmitTestfunction()
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn)
  const mutation =
    entity === 'experiment'
      ? experimentMut
      : entity === 'environment'
        ? environmentMut
        : testfunctionMut

  if (!isLoggedIn) return null

  const handleDelete = () => {
    if (entity === 'experiment') experimentMut.mutate({ name, action: 'remove' })
    else if (entity === 'environment') environmentMut.mutate({ name, action: 'remove' })
    else testfunctionMut.mutate({ name, action: 'remove' })
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link to={editTo} params={{ name }}>
            <Pencil className="w-3.5 h-3.5 mr-1" /> Edit
          </Link>
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setConfirming(true)}
          disabled={mutation.isPending || !!mutation.data}
        >
          <Trash2 className="w-3.5 h-3.5 mr-1" /> Delete
        </Button>
      </div>

      {mutation.data && (
        <Alert variant="success">
          <AlertDescription>
            Remove PR #{mutation.data.pr_number} opened. The {LABELS[entity]} is deleted once the PR
            is merged in Gitea.{' '}
            <a
              href={mutation.data.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="underline font-medium"
            >
              Open PR
            </a>
          </AlertDescription>
        </Alert>
      )}

      {mutation.error && (
        <Alert variant="destructive">
          <AlertDescription>
            {extractSubmitError(mutation.error, `Failed to remove ${LABELS[entity]}`)}
          </AlertDescription>
        </Alert>
      )}

      {confirming && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => !mutation.isPending && setConfirming(false)}
        >
          <Card className="w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <CardContent className="space-y-4 pt-6">
              <h3 className="font-display text-lg font-semibold">Delete {LABELS[entity]}?</h3>
              <p className="text-sm text-muted-foreground">
                This opens a remove pull request for <span className="font-mono">{name}</span>. The{' '}
                {LABELS[entity]} is only deleted once the PR is merged in Gitea.
              </p>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setConfirming(false)}
                  disabled={mutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    handleDelete()
                    setConfirming(false)
                  }}
                  disabled={mutation.isPending}
                >
                  {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
