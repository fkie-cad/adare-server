import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { WelcomeCard } from '../welcome-card'

vi.mock('@/api/hooks/use-stats', () => ({
  useStats: () => ({
    data: {
      run_count: 42,
      experiment_count: 10,
      testfunction_count: 5,
      user_count: 3,
      request_count: 7,
    },
  }),
}))

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  )
}

describe('WelcomeCard', () => {
  it('renders the welcome heading', () => {
    renderWithProviders(<WelcomeCard />)
    expect(screen.getByText('Welcome to ADARE')).toBeInTheDocument()
  })

  it('displays stat counts', () => {
    renderWithProviders(<WelcomeCard />)
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('displays stat labels', () => {
    renderWithProviders(<WelcomeCard />)
    expect(screen.getByText('Runs')).toBeInTheDocument()
    expect(screen.getByText('Experiments')).toBeInTheDocument()
    expect(screen.getByText('Testfunctions')).toBeInTheDocument()
  })
})
