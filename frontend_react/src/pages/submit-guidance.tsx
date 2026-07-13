import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { SubmitCode, extractSubmitFailure } from '@/pages/submit-shared'

interface SubmitGuidanceProps {
  error: unknown
  fallback: string
  /** When provided (create mode), renders a "submit a modify PR instead" action for ALREADY_PUBLISHED. */
  onSwitchToModify?: () => void
  isSwitching?: boolean
}

/**
 * Render a submit failure with category-specific guidance driven by the
 * server's ``code``:
 *   - ALREADY_PUBLISHED -> offer to switch to a modify PR (create mode only)
 *   - OPEN_DUPLICATE     -> point at the existing PR #M
 * Every other code just shows the precise server message so the user can fix
 * the files and re-push to the same PR.
 */
export function SubmitGuidance({ error, fallback, onSwitchToModify, isSwitching }: SubmitGuidanceProps) {
  const { message, code, pr_number } = extractSubmitFailure(error, fallback)
  return (
    <Alert variant="destructive" className="mb-4">
      <AlertDescription>
        <div>{message}</div>
        {code === SubmitCode.ALREADY_PUBLISHED && onSwitchToModify && (
          <div className="mt-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={onSwitchToModify}
              disabled={isSwitching}
            >
              Submit a modify PR instead
            </Button>
          </div>
        )}
        {code === SubmitCode.OPEN_DUPLICATE && pr_number != null && (
          <div className="mt-2 text-sm">
            Already proposed in pull request #{pr_number}. Update that PR instead of opening a new one.
          </div>
        )}
      </AlertDescription>
    </Alert>
  )
}
