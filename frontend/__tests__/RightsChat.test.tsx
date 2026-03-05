import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({ replace: vi.fn() })),
}))

vi.mock('@/lib/api', () => ({
  chat: vi.fn(),
}))

import { chat } from '@/lib/api'
import RightsChat from '@/components/RightsChat'
import type { ChatResponse } from '@/lib/types'

const SAMPLE_RESPONSE: ChatResponse = {
  answer:
    'Under CA Civil Code §1954, landlords must give 24-hour notice. Note: Not legal advice.',
  sources: ['https://sfrb.org/entry'],
  citations: ['CA Civil Code §1954'],
}

describe('RightsChat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders a text input field', () => {
    render(<RightsChat />)
    expect(screen.getByPlaceholderText(/ask about your tenant rights/i)).toBeInTheDocument()
  })

  it('renders a Send button', () => {
    render(<RightsChat />)
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('renders suggested starter questions', () => {
    render(<RightsChat />)
    expect(screen.getByText(/can my landlord raise my rent\?/i)).toBeInTheDocument()
  })

  it('disables the Send button while a request is loading', async () => {
    let resolveChat!: (v: ChatResponse) => void
    vi.mocked(chat).mockReturnValue(new Promise((res) => { resolveChat = res }))

    const user = userEvent.setup()
    render(<RightsChat />)

    const input = screen.getByPlaceholderText(/ask about your tenant rights/i)
    const sendBtn = screen.getByRole('button', { name: /send/i })

    await user.type(input, 'Test question')
    await user.click(sendBtn)

    await waitFor(() => {
      expect(sendBtn).toBeDisabled()
    })

    // Cleanup
    resolveChat(SAMPLE_RESPONSE)
  })

  it('renders the assistant answer and sources after API resolves', async () => {
    vi.mocked(chat).mockResolvedValue(SAMPLE_RESPONSE)

    const user = userEvent.setup()
    render(<RightsChat />)

    const input = screen.getByPlaceholderText(/ask about your tenant rights/i)
    const sendBtn = screen.getByRole('button', { name: /send/i })

    await user.type(input, 'What notice is required for entry?')
    await user.click(sendBtn)

    await waitFor(() => {
      expect(screen.getByText(/CA Civil Code §1954/i)).toBeInTheDocument()
    })
    expect(screen.getByText('https://sfrb.org/entry')).toBeInTheDocument()
  })

  it('shows an error message when the API call fails', async () => {
    vi.mocked(chat).mockRejectedValue(new Error('Network error'))

    const user = userEvent.setup()
    render(<RightsChat />)

    const input = screen.getByPlaceholderText(/ask about your tenant rights/i)
    await user.type(input, 'Test question')
    await user.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(screen.getByText(/⚠️ Error: Network error/i)).toBeInTheDocument()
    })
  })

  it('sends a message when Enter is pressed in the input', async () => {
    vi.mocked(chat).mockResolvedValue(SAMPLE_RESPONSE)

    const user = userEvent.setup()
    render(<RightsChat />)

    const input = screen.getByPlaceholderText(/ask about your tenant rights/i)
    await user.type(input, 'Deposit question{Enter}')

    await waitFor(() => {
      expect(vi.mocked(chat)).toHaveBeenCalledOnce()
    })
  })

  it('sends a message when a suggested question is clicked', async () => {
    vi.mocked(chat).mockResolvedValue(SAMPLE_RESPONSE)

    render(<RightsChat />)
    const suggestedBtn = screen.getByText(/can my landlord raise my rent\?/i)
    suggestedBtn.click()

    await waitFor(() => {
      expect(vi.mocked(chat)).toHaveBeenCalledOnce()
    })
  })
})
