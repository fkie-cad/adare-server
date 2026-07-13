import { useRef } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod/v4'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSubmitTestfunction } from '@/api/hooks/use-submit'
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
  testfunction: z.instanceof(FileList).optional(),
  requirements: z.instanceof(FileList).optional(),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

interface SubmitTestfunctionPageProps {
  mode?: 'create' | 'edit'
  name?: string
  currentFiles?: CurrentFile[]
}

export default function SubmitTestfunctionPage({
  mode = 'create',
  name: lockedName,
  currentFiles,
}: SubmitTestfunctionPageProps = {}) {
  const isEdit = mode === 'edit'
  const submitTestfunction = useSubmitTestfunction()
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
    const testfunction = data.testfunction?.[0]
    const requirements = data.requirements?.[0]
    if (!isEdit && (!testfunction || !requirements)) return
    if (isEdit && !testfunction && !requirements) return
    lastValues.current = data
    submitTestfunction.mutate({
      name: isEdit ? (lockedName as string) : data.name,
      testfunction,
      requirements,
      description: data.description,
      action: isEdit ? 'modify' : 'create',
    })
  }

  // ALREADY_PUBLISHED guidance action: re-submit the same upload as a modify PR.
  const switchToModify = () => {
    const data = lastValues.current
    if (!data) return
    submitTestfunction.mutate({
      name: data.name,
      testfunction: data.testfunction?.[0],
      requirements: data.requirements?.[0],
      description: data.description,
      action: 'modify',
    })
  }

  return (
    <div className="flex justify-center px-4 py-8">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <h2 className="font-display text-2xl font-bold tracking-tight">
            {isEdit ? `Edit Testfunction: ${lockedName}` : 'Submit Testfunction'}
          </h2>
          {isEdit && (
            <p className="text-sm text-muted-foreground">
              Upload only the file(s) you changed. This opens a modify pull request; it publishes
              once the PR is merged in Gitea.
            </p>
          )}
        </CardHeader>
        <CardContent>
          {submitTestfunction.data && (
            <Alert variant="success" className="mb-4">
              <AlertDescription>
                PR #{submitTestfunction.data.pr_number} created successfully.{' '}
                <a
                  href={submitTestfunction.data.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline font-medium"
                >
                  Open PR
                </a>
              </AlertDescription>
            </Alert>
          )}

          {submitTestfunction.error && (
            <SubmitGuidance
              error={submitTestfunction.error}
              fallback="Failed to submit testfunction"
              onSwitchToModify={isEdit ? undefined : switchToModify}
              isSwitching={submitTestfunction.isPending}
            />
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Testfunction Name</label>
              {isEdit ? (
                <Input value={lockedName} readOnly disabled />
              ) : (
                <>
                  <Input {...register('name')} placeholder="my-testfunction" />
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
                <Paperclip className="w-4 h-4" /> testfunction.py {isEdit && '(optional)'}
              </label>
              <Input type="file" accept=".py" {...register('testfunction')} />
            </div>

            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <Paperclip className="w-4 h-4" /> requirements.txt {isEdit && '(optional)'}
              </label>
              <Input type="file" accept=".txt" {...register('requirements')} />
            </div>

            <div>
              <label className="text-sm font-medium">Description / Notes</label>
              <Textarea
                {...register('description')}
                placeholder="Describe what you're submitting and why..."
                rows={4}
              />
            </div>

            <Button type="submit" disabled={submitTestfunction.isPending}>
              {submitTestfunction.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
              {isEdit ? 'Submit changes' : 'Submit'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
