import { useForm } from 'react-hook-form'
import { z } from 'zod/v4'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSubmitEnvironment } from '@/api/hooks/use-submit'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Paperclip } from 'lucide-react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  environment: z.instanceof(FileList).refine((f) => f.length > 0, 'Environment file is required'),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export default function SubmitEnvironmentPage() {
  const submitEnvironment = useSubmitEnvironment()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormValues) => {
    submitEnvironment.mutate({
      name: data.name,
      environment: data.environment[0],
      description: data.description,
    })
  }

  return (
    <div className="flex justify-center py-8">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <h2 className="text-2xl font-bold">Submit Environment</h2>
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
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>
                {(submitEnvironment.error as Error).message || 'Failed to submit environment'}
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Environment Name</label>
              <Input {...register('name')} placeholder="my-environment" />
              {errors.name && <p className="text-sm text-destructive mt-1">{errors.name.message}</p>}
            </div>

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
              Submit
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
