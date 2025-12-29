import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { ChatInterface } from '@/components/chat-interface'
import { aiAgent } from '@/lib/ai-agent-client'

// Mock the AI Agent client
jest.mock('@/lib/ai-agent-client', () => ({
  aiAgent: {
    chatStream: jest.fn(),
  },
}))

// ReactMarkdown is mocked via __mocks__ directory

describe('ChatInterface', () => {
  const mockChatStream = aiAgent.chatStream as jest.MockedFunction<typeof aiAgent.chatStream>

  // Helper to find send button
  const getSendButton = () => {
    const buttons = screen.getAllByRole('button')
    return buttons.find(btn => btn.querySelector('svg') && !btn.disabled) || buttons[0]
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<ChatInterface />)
    expect(screen.getByText('AI Agent Chat')).toBeInTheDocument()
  })

  it('renders input field', () => {
    render(<ChatInterface />)
    expect(
      screen.getByPlaceholderText(
        'Ask a question about policies, claims, customers, or company info...'
      )
    ).toBeInTheDocument()
  })

  it('allows user to type a message', () => {
    render(<ChatInterface />)
    const input = screen.getByPlaceholderText(
      'Ask a question about policies, claims, customers, or company info...'
    ) as HTMLInputElement

    fireEvent.change(input, { target: { value: 'Test question' } })
    expect(input.value).toBe('Test question')
  })

  it('sends message and receives response', async () => {
    mockChatStream.mockImplementation(async (request, onChunk, onComplete) => {
      onChunk('Response text')
      onComplete({
        sources: ['../data/knowledge-base/company/website.pdf'],
        query_type: 'rag',
      })
    })

    render(<ChatInterface />)
    const input = screen.getByPlaceholderText(
      'Ask a question about policies, claims, customers, or company info...'
    )
    const sendButton = getSendButton()

    fireEvent.change(input, { target: { value: 'Test question' } })
    fireEvent.click(sendButton)

    // Wait for response to appear
    await waitFor(() => {
      const response = screen.queryByText(/Response text/i)
      expect(response).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('prevents sending empty messages', () => {
    render(<ChatInterface />)
    const input = screen.getByPlaceholderText(
      'Ask a question about policies, claims, customers, or company info...'
    )
    const sendButton = getSendButton()

    // Button should be disabled when input is empty
    expect(sendButton).toBeDisabled()

    // Type content
    fireEvent.change(input, { target: { value: 'test' } })
    expect(sendButton).not.toBeDisabled()
  })

  it('sends correct request parameters', async () => {
    let capturedRequest: any

    mockChatStream.mockImplementation(async (request, onChunk, onComplete) => {
      capturedRequest = request
      onChunk('Response')
      onComplete({ sources: [], query_type: 'rag' })
    })

    render(<ChatInterface />)
    const input = screen.getByPlaceholderText(
      'Ask a question about policies, claims, customers, or company info...'
    )
    const sendButton = getSendButton()

    fireEvent.change(input, { target: { value: 'Test question' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(capturedRequest).toBeDefined()
      expect(capturedRequest.user_id).toBe('admin')
      expect(capturedRequest.temperature).toBe(0.1)
      expect(capturedRequest.top_k).toBe(3)
    }, { timeout: 3000 })
  })
})
