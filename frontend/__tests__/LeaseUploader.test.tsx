import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}))

// Mock the API module before importing the component
vi.mock('@/lib/api', () => ({
  analyzeLease: vi.fn(),
}))

import { analyzeLease } from '@/lib/api'
import LeaseUploader from '@/components/LeaseUploader'
import type { AnalyzeResponse } from '@/lib/types'

const SAMPLE_RESPONSE: AnalyzeResponse = {
  session_id: 'test-session',
  illegal_clauses: [],
  total_clauses_scanned: 5,
  risk_score: 20,
  summary: 'Lease looks fine.',
}

/** Fire a change event on the hidden file input with the given File(s). */
function uploadFiles(files: File[]) {
  const input = document.getElementById('pdf-input') as HTMLInputElement
  // Define `files` on the input's event target (required for JSDOM/happy-dom)
  Object.defineProperty(input, 'files', {
    value: files,
    configurable: true,
  })
  fireEvent.change(input)
}

describe('LeaseUploader', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('renders a file input element', () => {
    render(<LeaseUploader />)
    const input = document.getElementById('pdf-input') as HTMLInputElement
    expect(input).not.toBeNull()
    expect(input.type).toBe('file')
    expect(input.accept).toBe('.pdf')
  })

  it('renders the Analyze Lease submit button', () => {
    render(<LeaseUploader />)
    expect(screen.getByRole('button', { name: /analyze lease/i })).toBeInTheDocument()
  })

  it('shows an error when a non-PDF file is selected', () => {
    render(<LeaseUploader />)
    const txtFile = new File(['hello'], 'document.txt', { type: 'text/plain' })
    uploadFiles([txtFile])
    expect(screen.getByText('Only PDF files are accepted.')).toBeInTheDocument()
  })

  it('shows an error when a file larger than 10 MB is selected', () => {
    render(<LeaseUploader />)
    const pdfFile = new File(['%PDF-1.4 content'], 'big.pdf', { type: 'application/pdf' })
    Object.defineProperty(pdfFile, 'size', { value: 11 * 1024 * 1024, configurable: true })
    uploadFiles([pdfFile])
    expect(screen.getByText(/maximum is 10 MB/i)).toBeInTheDocument()
  })

  it('accepts a valid PDF and enables the Analyze Lease button', () => {
    render(<LeaseUploader />)
    const pdfFile = new File(['%PDF-1.4 content'], 'lease.pdf', { type: 'application/pdf' })
    uploadFiles([pdfFile])
    const btn = screen.getByRole('button', { name: /analyze lease/i })
    expect(btn).not.toBeDisabled()
  })

  it('shows loading state while the upload API is in progress', async () => {
    let resolveUpload!: (v: AnalyzeResponse) => void
    vi.mocked(analyzeLease).mockReturnValue(new Promise((res) => { resolveUpload = res }))

    render(<LeaseUploader />)
    const pdfFile = new File(['%PDF content'], 'lease.pdf', { type: 'application/pdf' })
    uploadFiles([pdfFile])

    fireEvent.click(screen.getByRole('button', { name: /analyze lease/i }))

    await waitFor(() => {
      expect(screen.getByText(/analyzing…/i)).toBeInTheDocument()
    })

    // Cleanup: resolve the promise
    resolveUpload(SAMPLE_RESPONSE)
  })

  it('shows an error message when the API returns an error', async () => {
    vi.mocked(analyzeLease).mockRejectedValue(new Error('Server error'))

    render(<LeaseUploader />)
    const pdfFile = new File(['%PDF content'], 'lease.pdf', { type: 'application/pdf' })
    uploadFiles([pdfFile])

    fireEvent.click(screen.getByRole('button', { name: /analyze lease/i }))

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument()
    })
  })
})
