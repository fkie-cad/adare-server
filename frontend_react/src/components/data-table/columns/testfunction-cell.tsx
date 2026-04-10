import type { Testfunction } from '@/types/experiment'

interface TestfunctionCellProps {
  testfunction: Testfunction
}

export function TestfunctionCell({ testfunction }: TestfunctionCellProps) {
  if (!testfunction) return null
  return <span className="text-sm">{testfunction.set}.{testfunction.name}</span>
}
