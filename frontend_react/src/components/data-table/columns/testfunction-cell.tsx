import type { Testfunction } from '@/types/experiment'

interface TestfunctionCellProps {
  testfunction: Testfunction
}

export function TestfunctionCell({ testfunction }: TestfunctionCellProps) {
  if (!testfunction) return null
  // `name` is already the qualified `<set>.<name>` identity a playbook writes in
  // `function:` (see the server's plugin.qualify_test_name); prefixing `set`
  // again would render `jsonl.jsonl.line_matches`. Older rows may still be bare,
  // so fall back to prefixing when the name carries no set.
  const label = testfunction.name.includes('.')
    ? testfunction.name
    : `${testfunction.set}.${testfunction.name}`
  return <span className="text-sm">{label}</span>
}
