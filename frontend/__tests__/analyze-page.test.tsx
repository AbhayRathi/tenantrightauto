import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock next/navigation before any component imports
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

// Mock all child components that have heavy deps (react-force-graph etc.)
vi.mock('@/components/ClauseAnalysis', () => ({ default: () => <div data-testid="clause-analysis" /> }))
vi.mock('@/components/RightsChat', () => ({ default: () => <div data-testid="rights-chat" /> }))
vi.mock('@/components/DemandLetter', () => ({ default: () => <div data-testid="demand-letter" /> }))
vi.mock('@/components/Neo4jGraph', () => ({ default: () => <div data-testid="neo4j-graph" /> }))

import { useRouter } from 'next/navigation'
import AnalyzePage from '@/app/analyze/page'

const SAMPLE_DATA = {
  session_id: 'abc-123',
  illegal_clauses: [],
  total_clauses_scanned: 10,
  risk_score: 25,
  summary: 'No major issues found.',
}

describe('AnalyzePage', () => {
  const mockReplace = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    vi.mocked(useRouter).mockReturnValue({ replace: mockReplace } as ReturnType<typeof useRouter>)
  })

  it('calls router.replace("/") when sessionStorage has no analyzeResult', async () => {
    render(<AnalyzePage />)
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/')
    })
  })

  it('renders the dashboard when sessionStorage has valid JSON', async () => {
    sessionStorage.setItem('analyzeResult', JSON.stringify(SAMPLE_DATA))
    render(<AnalyzePage />)
    await waitFor(() => {
      expect(screen.getByText('Lease Analysis Results')).toBeInTheDocument()
    })
    expect(mockReplace).not.toHaveBeenCalled()
  })

  it('calls router.replace("/") when sessionStorage JSON is invalid/corrupt', async () => {
    sessionStorage.setItem('analyzeResult', 'not-valid-json{{{')
    render(<AnalyzePage />)
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/')
    })
  })

  it('displays the risk score badge from session data', async () => {
    sessionStorage.setItem('analyzeResult', JSON.stringify({ ...SAMPLE_DATA, risk_score: 85 }))
    render(<AnalyzePage />)
    await waitFor(() => {
      expect(screen.getByText(/High Risk/i)).toBeInTheDocument()
    })
  })

  it('shows a low risk badge when score < 30', async () => {
    sessionStorage.setItem('analyzeResult', JSON.stringify({ ...SAMPLE_DATA, risk_score: 10 }))
    render(<AnalyzePage />)
    await waitFor(() => {
      expect(screen.getByText(/Low Risk/i)).toBeInTheDocument()
    })
  })

  it('useState lazy initializer reads sessionStorage synchronously (no extra render needed)', () => {
    sessionStorage.setItem('analyzeResult', JSON.stringify(SAMPLE_DATA))
    // If the lazy initializer works, the component renders with data on the first pass
    // without needing an async effect to set state
    const { container } = render(<AnalyzePage />)
    // The component should NOT show the Loading fallback when data is present
    expect(container.innerHTML).not.toContain('Loading')
    expect(mockReplace).not.toHaveBeenCalled()
  })
})
