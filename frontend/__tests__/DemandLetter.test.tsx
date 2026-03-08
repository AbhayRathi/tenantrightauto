import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('@/lib/api', () => ({
  generateLetter: vi.fn(),
}))

import { generateLetter } from '@/lib/api'
import DemandLetter from '@/components/DemandLetter'
import type { IllegalClause, DemandLetterResponse } from '@/lib/types'

const SAMPLE_CLAUSE: IllegalClause = {
  clause_text: 'Tenant waives habitability.',
  violation_type: 'Habitability waiver',
  legal_citation: 'CA Civil Code §1941',
  severity: 'high',
  remedy: 'Clause is void.',
  explanation: 'Cannot waive habitability.',
}

const SAMPLE_RESPONSE: DemandLetterResponse = {
  letter_text: 'Dear Mr. Smith, your lease contains illegal clauses under CA law.',
  generated_at: '2026-01-01T00:00:00Z',
}

describe('DemandLetter', () => {
  const defaultProps = {
    sessionId: 'test-session',
    selectedClauses: [SAMPLE_CLAUSE],
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // happy-dom defines clipboard as a non-writable property, so use defineProperty
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      writable: true,
      configurable: true,
    })
    // Stub URL blob methods
    global.URL.createObjectURL = vi.fn(() => 'blob:test-url')
    global.URL.revokeObjectURL = vi.fn()
  })

  it('renders the tenant name input', () => {
    render(<DemandLetter {...defaultProps} />)
    expect(screen.getByPlaceholderText('Jane Doe')).toBeInTheDocument()
  })

  it('renders the tenant address input', () => {
    render(<DemandLetter {...defaultProps} />)
    expect(screen.getByPlaceholderText('123 Main St, SF, CA 94102')).toBeInTheDocument()
  })

  it('renders the landlord name input', () => {
    render(<DemandLetter {...defaultProps} />)
    expect(screen.getByPlaceholderText('Bob Smith')).toBeInTheDocument()
  })

  it('renders the landlord address input', () => {
    render(<DemandLetter {...defaultProps} />)
    expect(screen.getByPlaceholderText('456 Oak Ave, SF, CA 94110')).toBeInTheDocument()
  })

  it('renders the remedy requested textarea', () => {
    render(<DemandLetter {...defaultProps} />)
    expect(
      screen.getByPlaceholderText(/remove clause 5 regarding security deposit/i),
    ).toBeInTheDocument()
  })

  it('calls generateLetter with the correct payload when Generate button is clicked', async () => {
    vi.mocked(generateLetter).mockResolvedValue(SAMPLE_RESPONSE)

    const user = userEvent.setup()
    render(<DemandLetter {...defaultProps} />)

    await user.type(screen.getByPlaceholderText('Jane Doe'), 'Jane Doe')
    await user.type(screen.getByPlaceholderText('123 Main St, SF, CA 94102'), '123 Main St')
    await user.type(screen.getByPlaceholderText('Bob Smith'), 'Bob Smith')
    await user.type(screen.getByPlaceholderText('456 Oak Ave, SF, CA 94110'), '456 Oak Ave')

    fireEvent.click(screen.getByRole('button', { name: /generate demand letter/i }))

    await waitFor(() => {
      expect(vi.mocked(generateLetter)).toHaveBeenCalledWith(
        expect.objectContaining({
          session_id: 'test-session',
          tenant_name: 'Jane Doe',
          illegal_clauses: [SAMPLE_CLAUSE],
        }),
      )
    })
  })

  it('renders the generated letter text after API resolves', async () => {
    vi.mocked(generateLetter).mockResolvedValue(SAMPLE_RESPONSE)

    render(<DemandLetter {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /generate demand letter/i }))

    await waitFor(() => {
      expect(screen.getByText(/Dear Mr. Smith/)).toBeInTheDocument()
    })
  })

  it('shows the Download button after letter is generated', async () => {
    vi.mocked(generateLetter).mockResolvedValue(SAMPLE_RESPONSE)

    render(<DemandLetter {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /generate demand letter/i }))

    await waitFor(() => {
      expect(screen.getByText(/⬇️ Download \.txt/i)).toBeInTheDocument()
    })
  })

  it('triggers a blob download when the Download button is clicked', async () => {
    vi.mocked(generateLetter).mockResolvedValue(SAMPLE_RESPONSE)

    render(<DemandLetter {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /generate demand letter/i }))

    await waitFor(() => screen.getByText(/⬇️ Download \.txt/i))
    fireEvent.click(screen.getByText(/⬇️ Download \.txt/i))

    expect(global.URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob))
  })

  it('shows a warning and disables the button when no clauses are selected', () => {
    render(<DemandLetter sessionId="test" selectedClauses={[]} />)
    // The component shows a pre-render warning and disables the Generate button
    expect(screen.getByText(/No clauses selected/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /generate demand letter/i })).toBeDisabled()
  })
})
