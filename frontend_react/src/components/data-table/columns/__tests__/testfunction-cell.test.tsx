import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { TestfunctionCell } from '../testfunction-cell'
import type { Testfunction } from '@/types/experiment'

function testfunction(overrides: Partial<Testfunction>): Testfunction {
  return {
    name: 'line_matches',
    description: '',
    possible_parameters: [],
    set: 'jsonl',
    ...overrides,
  }
}

describe('TestfunctionCell', () => {
  it('renders an already-qualified name as-is', () => {
    render(<TestfunctionCell testfunction={testfunction({ name: 'jsonl.line_matches' })} />)
    expect(screen.getByText('jsonl.line_matches')).toBeInTheDocument()
    expect(screen.queryByText('jsonl.jsonl.line_matches')).toBeNull()
  })

  it('prefixes the set for a legacy bare name', () => {
    render(<TestfunctionCell testfunction={testfunction({ name: 'line_matches' })} />)
    expect(screen.getByText('jsonl.line_matches')).toBeInTheDocument()
  })
})
