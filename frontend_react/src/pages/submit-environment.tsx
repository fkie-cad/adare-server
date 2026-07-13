import { useRef } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod/v4'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSubmitEnvironment } from '@/api/hooks/use-submit'
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
  environment: z.instanceof(FileList).refine((f) => f.length > 0, 'Environment file is required'),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

interface SubmitEnvironmentPageProps {
  mode?: 'create' | 'edit'
  name?: string
  currentFiles?: CurrentFile[]
}

export default function SubmitEnvironmentPage({
  mode = 'create',
  name: lockedName,
  currentFiles,
}: SubmitEnvironmentPageProps = {}) {
  const isEdit = mode === 'edit'
  const submitEnvironment = useSubmitEnvironment()
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
    lastValues.current = data
    submitEnvironment.mutate({
      name: isEdit ? (lockedName as string) : data.name,
      environment: data.environment[0],
      description: data.description,
      action: isEdit ? 'modify' : 'create',
    })
  }

  // ALREADY_PUBLISHED guidance action: re-submit the same upload as a modify PR.
  const switchToModify = () => {
    const data = lastValues.current
    if (!data) return
    submitEnvironment.mutate({
      name: data.name,
      environment: data.environment[0],
      description: data.description,
      action: 'modify',
    })
  }

  return (
    <div className="flex justify-center px-4 py-8">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <h2 className="font-display text-2xl font-bold tracking-tight">
            {isEdit ? `Edit Environment: ${lockedName}` : 'Submit Environment'}
          </h2>
          {isEdit && (
            <p className="text-sm text-muted-foreground">
              Upload the updated environment file. This opens a modify pull request; it publishes
              once the PR is merged in Gitea.
            </p>
          )}
        </CardHeader>
        <CardContent>
          {submitEnvironment.data && (
            <Alert variant="success" className="mb-4">
              <AlertDescription>
                PR #{submitEnvironment.data.pr_number} created successfully.{' '}
                <a
                  href={submitEnvironment.data.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline font-medium"
                >
                  Open PR
                </a>
              </AlertDescription>
            </Alert>
          )}

          {submitEnvironment.error && (
            <SubmitGuidance
              error={submitEnvironment.error}
              fallback="Failed to submit environment"
              onSwitchToModify={isEdit ? undefined : switchToModify}
              isSwitching={submitEnvironment.isPending}
            />
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Environment Name</label>
              {isEdit ? (
                <Input value={lockedName} readOnly disabled />
              ) : (
                <>
                  <Input {...register('name')} placeholder="my-environment" />
                  {errors.name && (
                    <p className="text-sm text-destructive mt-1">{errors.name.message}</p>
                  )}
                </>
              )}
            </div>

            {isEdit && currentFiles && currentFiles.length > 0 && (
              <div className="rounded-md border bg-muted/40 p-3 text-sm">
                <div className="mb-1 text-muted-foreground">current file</div>
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
                <Paperclip className="w-4 h-4" /> environment.yml
              </label>
              <Input type="file" accept=".yml,.yaml" {...register('environment')} />
              {errors.environment && (
                <p className="text-sm text-destructive mt-1">{errors.environment.message}</p>
              )}
            </div>

            <div>
              <label className="text-sm font-medium">Description / Notes</label>
              <Textarea
                {...register('description')}
                placeholder="Describe what you're submitting and why..."
                rows={4}
              />
            </div>

            <Button type="submit" disabled={submitEnvironment.isPending}>
              {submitEnvironment.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
              {isEdit ? 'Submit changes' : 'Submit'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
