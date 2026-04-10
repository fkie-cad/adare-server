import { useForm } from 'react-hook-form'
import { z } from 'zod/v4'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSubmitTestfunction } from '@/api/hooks/use-submit'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Paperclip } from 'lucide-react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  testfunction: z.instanceof(FileList).refine((f) => f.length > 0, 'Testfunction file is required'),
  requirements: z.instanceof(FileList).refine((f) => f.length > 0, 'Requirements file is required'),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export default function SubmitTestfunctionPage() {
  const submitTestfunction = useSubmitTestfunction()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormValues) => {
    submitTestfunction.mutate({
      name: data.name,
      testfunction: data.testfunction[0],
      requirements: data.requirements[0],
      description: data.description,
    })
  }

  return (
    <div className="flex justify-center py-8">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <h2 className="text-2xl font-bold">Submit Testfunction</h2>
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
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>
                {(submitTestfunction.error as Error).message || 'Failed to submit testfunction'}
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Testfunction Name</label>
              <Input {...register('name')} placeholder="my-testfunction" />
              {errors.name && <p className="text-sm text-destructive mt-1">{errors.name.message}</p>}
            </div>

            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <Paperclip className="w-4 h-4" /> testfunction.py
              </label>
              <Input type="file" accept=".py" {...register('testfunction')} />
              {errors.testfunction && (
                <p className="text-sm text-destructive mt-1">{errors.testfunction.message}</p>
              )}
            </div>

            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <Paperclip className="w-4 h-4" /> requirements.txt
              </label>
              <Input type="file" accept=".txt" {...register('requirements')} />
              {errors.requirements && (
                <p className="text-sm text-destructive mt-1">{errors.requirements.message}</p>
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

            <Button type="submit" disabled={submitTestfunction.isPending}>
              {submitTestfunction.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
              Submit
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
