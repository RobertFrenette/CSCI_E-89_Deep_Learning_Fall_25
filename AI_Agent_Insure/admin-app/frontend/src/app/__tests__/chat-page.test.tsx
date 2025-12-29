import { render, screen } from '@testing-library/react'
import ChatPage from '@/app/chat/page'
import { SidebarProvider } from '@/components/ui/sidebar'

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  usePathname: () => '/chat',
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}))

// Mock the AI Agent client
jest.mock('@/lib/ai-agent-client', () => ({
  aiAgent: {
    chatStream: jest.fn(),
  },
}))

// ReactMarkdown is mocked via __mocks__ directory

describe('ChatPage - E2E Integration', () => {
  const renderWithProvider = (ui: React.ReactElement) => {
    return render(<SidebarProvider>{ui}</SidebarProvider>)
  }

  it('renders chat page', () => {
    renderWithProvider(<ChatPage />)
    const chatTitles = screen.getAllByText('AI Agent Chat')
    expect(chatTitles.length).toBeGreaterThan(0)
  })

  it('renders input field', () => {
    renderWithProvider(<ChatPage />)
    expect(
      screen.getByPlaceholderText(
        'Ask a question about policies, claims, customers, or company info...'
      )
    ).toBeInTheDocument()
  })

  it('renders chat interface component', () => {
    renderWithProvider(<ChatPage />)
    // ChatInterface should render its title (multiple instances exist)
    const titles = screen.getAllByText('AI Agent Chat')
    expect(titles.length).toBeGreaterThan(0)
  })
})
