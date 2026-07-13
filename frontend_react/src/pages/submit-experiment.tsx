import { useRef } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod/v4'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSubmitExperiment } from '@/api/hooks/use-submit'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Paperclip, ExternalLink } from 'lucide-react'
import { type CurrentFile } from '@/pages/submit-shared'
import { SubmitGuidance } from '@/pages/submit-guidance'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  playbook: z.instanceof(FileList).optional(),
  metadata: z.instanceof(FileList).optional(),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

interface SubmitExperimentPageProps {
  mode?: 'create' | 'edit'
  name?: string
  currentFiles?: CurrentFile[]
}

export default function SubmitExperimentPage({
  mode = 'create',
  name: lockedName,
  currentFiles,
}: SubmitExperimentPageProps = {}) {
  const isEdit = mode === 'edit'
  const submitExperiment = useSubmitExperiment()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: lockedName },
  })

  const lastValues = useRef<FormValues | null>(null)

  const onSubmit = (data: FormValues) => {
    const playbook = data.playbook?.[0]
    const metadata = data.metadata?.[0]
    if (!isEdit && (!playbook || !metadata)) return
    if (isEdit && !playbook && !metadata) return
    lastValues.current = data
    submitExperiment.mutate({
      name: isEdit ? (lockedName as string) : data.name,
      playbook,
      metadata,
      description: data.description,
      action: isEdit ? 'modify' : 'create',
    })
  }

  // ALREADY_PUBLISHED guidance action: re-submit the same upload as a modify PR.
  const switchToModify = () => {
    const data = lastValues.current
    if (!data) return
    submitExperiment.mutate({
      name: data.name,
      playbook: data.playbook?.[0],
      metadata: data.metadata?.[0],
      description: data.description,
      action: 'modify',
    })
  }

  return (
    <div className="flex justify-center px-4 py-8">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <h2 className="font-display text-2xl font-bold tracking-tight">
            {isEdit ? `Edit Experiment: ${lockedName}` : 'Submit Experiment'}
          </h2>
          {isEdit && (
            <p className="text-sm text-muted-foreground">
              Upload only the file(s) you changed. This opens a modify pull request; it publishes
              once the PR is merged in Gitea.
            </p>
          )}
        </CardHeader>
        <CardContent>
          {submitExperiment.data && (
            <Alert variant="success" className="mb-4">
              <AlertDescription>
                PR #{submitExperiment.data.pr_number} created successfully.{' '}
                <a
                  href={submitExperiment.data.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline font-medium"
                >
                  Open PR
                </a>
              </AlertDescription>
            </Alert>
          )}

          {submitExperiment.error && (
            <SubmitGuidance
              error={submitExperiment.error}
              fallback="Failed to submit experiment"
              onSwitchToModify={isEdit ? undefined : switchToModify}
              isSwitching={submitExperiment.isPending}
            />
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Experiment Name</label>
              {isEdit ? (
                <Input value={lockedName} readOnly disabled />
              ) : (
                <>
                  <Input {...register('name')} placeholder="my-experiment" />
                  {errors.name && (
                    <p className="text-sm text-destructive mt-1">{errors.name.message}</p>
                  )}
                </>
              )}
            </div>

            {isEdit && currentFiles && currentFiles.length > 0 && (
              <div className="rounded-md border bg-muted/40 p-3 text-sm">
                <div className="mb-1 text-muted-foreground">current files</div>
                <div className="flex flex-wrap gap-3">
                  {currentFiles.map((f) => (
                    <a
                      key={f.label}
                      href={f.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 underline"
                    >
                      {f.label} <ExternalLink className="w-3 h-3" />
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <Paperclip className="w-4 h-4" /> playbook.yml {isEdit && '(optional)'}
              </label>
              <Input type="file" accept=".yml,.yaml" {...register('playbook')} />
            </div>

            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <Paperclip className="w-4 h-4" /> metadata.yml {isEdit && '(optional)'}
              </label>
              <Input type="file" accept=".yml,.yaml" {...register('metadata')} />
            </div>

            <div>
              <label className="text-sm font-medium">Description / Notes</label>
              <Textarea
                {...register('description')}
                placeholder="Describe what you're submitting and why..."
                rows={4}
              />
            </div>

            <Button type="submit" disabled={submitExperiment.isPending}>
              {submitExperiment.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
              {isEdit ? 'Submit changes' : 'Submit'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
