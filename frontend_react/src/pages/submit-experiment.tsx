import { useForm } from 'react-hook-form'
import { z } from 'zod/v4'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSubmitExperiment } from '@/api/hooks/use-submit'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Paperclip } from 'lucide-react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  playbook: z.instanceof(FileList).refine((f) => f.length > 0, 'Playbook file is required'),
  metadata: z.instanceof(FileList).refine((f) => f.length > 0, 'Metadata file is required'),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export default function SubmitExperimentPage() {
  const submitExperiment = useSubmitExperiment()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormValues) => {
    submitExperiment.mutate({
      name: data.name,
      playbook: data.playbook[0],
      metadata: data.metadata[0],
      description: data.description,
    })
  }

  return (
    <div className="flex justify-center px-4 py-8">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <h2 className="font-display text-2xl font-bold tracking-tight">Submit Experiment</h2>
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
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>
                {(submitExperiment.error as Error).message || 'Failed to submit experiment'}
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Experiment Name</label>
              <Input {...register('name')} placeholder="my-experiment" />
              {errors.name && <p className="text-sm text-destructive mt-1">{errors.name.message}</p>}
            </div>

            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <Paperclip className="w-4 h-4" /> playbook.yml
              </label>
              <Input type="file" accept=".yml,.yaml" {...register('playbook')} />
              {errors.playbook && (
                <p className="text-sm text-destructive mt-1">{errors.playbook.message}</p>
              )}
            </div>

            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <Paperclip className="w-4 h-4" /> metadata.yml
              </label>
              <Input type="file" accept=".yml,.yaml" {...register('metadata')} />
              {errors.metadata && (
                <p className="text-sm text-destructive mt-1">{errors.metadata.message}</p>
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

            <Button type="submit" disabled={submitExperiment.isPending}>
              {submitExperiment.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
              Submit
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
