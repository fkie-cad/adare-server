import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StatusIcon } from '../status-icon'
import { isValidStatusType, statusColorMapping } from '@/constants/mappings'

describe('StatusIcon', () => {
  it('treats inconclusive as a known status with the amber warning colour', () => {
    expect(isValidStatusType('inconclusive')).toBe(true)
    expect(statusColorMapping.inconclusive).toBe('text-warning')

    const { container } = render(<StatusIcon status="inconclusive" showTooltip={false} />)
    const svg = container.querySelector('svg')
    expect(svg?.getAttribute('class')).toContain('text-warning')
    expect(svg?.getAttribute('class')).not.toContain('text-success')
  })

  it('falls back to the muted help icon for an unknown status', () => {
    const { container } = render(<StatusIcon status="bogus" showTooltip={false} />)
    expect(container.querySelector('svg')?.getAttribute('class')).toContain('text-muted-foreground')
  })
})
