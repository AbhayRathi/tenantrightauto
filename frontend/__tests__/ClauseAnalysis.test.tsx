import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ClauseAnalysis from '@/components/ClauseAnalysis'
import type { IllegalClause } from '@/lib/types'

function makeClause(overrides: Partial<IllegalClause> = {}): IllegalClause {
  return {
    clause_text: 'Tenant waives habitability rights.',
    violation_type: 'Habitability waiver',
    legal_citation: 'CA Civil Code §1941',
    severity: 'high',
    remedy: 'Clause is void.',
    explanation: 'Cannot waive the implied warranty of habitability.',
    ...overrides,
  }
}

describe('ClauseAnalysis', () => {
  const noOp = () => {}

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders a no-issues message when clauses array is empty', () => {
    render(<ClauseAnalysis clauses={[]} selectedClauses={[]} onSelectionChange={noOp} />)
    expect(screen.getByText(/no illegal clauses detected/i)).toBeInTheDocument()
  })

  it('renders all clauses passed as props', () => {
    const clauses = [
      makeClause({ violation_type: 'Habitability waiver' }),
      makeClause({ violation_type: 'Security deposit excess', severity: 'medium' }),
    ]
    render(<ClauseAnalysis clauses={clauses} selectedClauses={[]} onSelectionChange={noOp} />)
    expect(screen.getByText('Habitability waiver')).toBeInTheDocument()
    expect(screen.getByText('Security deposit excess')).toBeInTheDocument()
  })

  it('shows a red badge for high-severity clauses', () => {
    render(
      <ClauseAnalysis
        clauses={[makeClause({ severity: 'high' })]}
        selectedClauses={[]}
        onSelectionChange={noOp}
      />,
    )
    const badge = screen.getByText('high')
    expect(badge.className).toMatch(/bg-red/)
  })

  it('shows an orange badge for medium-severity clauses', () => {
    render(
      <ClauseAnalysis
        clauses={[makeClause({ severity: 'medium' })]}
        selectedClauses={[]}
        onSelectionChange={noOp}
      />,
    )
    const badge = screen.getByText('medium')
    expect(badge.className).toMatch(/bg-orange/)
  })

  it('shows a yellow badge for low-severity clauses', () => {
    render(
      <ClauseAnalysis
        clauses={[makeClause({ severity: 'low' })]}
        selectedClauses={[]}
        onSelectionChange={noOp}
      />,
    )
    const badge = screen.getByText('low')
    expect(badge.className).toMatch(/bg-yellow/)
  })

  it('displays violation type and legal citation in the header row', () => {
    const clause = makeClause({ violation_type: 'Entry without notice', legal_citation: 'CA Civil Code §1954' })
    render(<ClauseAnalysis clauses={[clause]} selectedClauses={[]} onSelectionChange={noOp} />)
    expect(screen.getByText('Entry without notice')).toBeInTheDocument()
    expect(screen.getByText('CA Civil Code §1954')).toBeInTheDocument()
  })

  it('reveals clause text and explanation after expanding a card', () => {
    const clause = makeClause({ clause_text: 'Waiver of habitability.', explanation: 'This is illegal.' })
    render(<ClauseAnalysis clauses={[clause]} selectedClauses={[]} onSelectionChange={noOp} />)
    // Expand card by clicking the header button
    const expandBtn = screen.getByRole('button', { name: /Habitability waiver/i })
    fireEvent.click(expandBtn)
    expect(screen.getByText('Waiver of habitability.')).toBeInTheDocument()
    expect(screen.getByText('This is illegal.')).toBeInTheDocument()
  })

  it('calls onSelectionChange when a clause checkbox is toggled', () => {
    const clause = makeClause()
    const onSelectionChange = vi.fn()
    render(
      <ClauseAnalysis clauses={[clause]} selectedClauses={[]} onSelectionChange={onSelectionChange} />,
    )
    const checkbox = screen.getByRole('checkbox', { name: /Select clause: Habitability waiver/i })
    fireEvent.click(checkbox)
    expect(onSelectionChange).toHaveBeenCalledWith([clause])
  })
})
