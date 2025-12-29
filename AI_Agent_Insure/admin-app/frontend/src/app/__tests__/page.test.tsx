import { render, screen } from '@testing-library/react'
import { SidebarProvider } from '@/components/ui/sidebar'

// Mock the API module
jest.mock('@/lib/api', () => ({
  api: {
    getDashboardStats: jest.fn(),
  },
}))

// Mock the components
jest.mock('@/components/policy-type-chart', () => ({
  PolicyTypeChart: ({ data }: any) => <div data-testid="policy-type-chart">Policy Chart</div>,
}))

jest.mock('@/components/recent-claims', () => ({
  RecentClaims: ({ claims }: any) => <div data-testid="recent-claims">Recent Claims</div>,
}))

// Import after mocks are defined
import DashboardPage from '@/app/page'
import { api } from '@/lib/api'

describe('DashboardPage', () => {
  const mockStats = {
    overview: {
      total_customers: 500,
      active_policies: 750,
      total_policies: 800,
      active_claims: 45,
      total_claims: 120,
      total_premium_value: '2500000',
      average_policy_value: '3125',
    },
    policyByType: [
      {
        policy_type: 'Auto Insurance',
        count: '300',
        total_premium: '750000',
      },
    ],
    aiSystemTypes: [
      {
        ai_system_type: 'LLM',
        count: 10,
        avg_risk_score: 42.5,
      },
    ],
    recentClaims: [
      {
        claim_id: 'CLM-001',
        claim_date: '2024-01-15T00:00:00Z',
        claim_type: 'Auto',
        claim_status: 'Open',
        claim_amount: '5000',
        company_name: 'Acme Corp',
        policy_type: 'Auto Insurance',
      },
    ],
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  function renderWithProvider(component: React.ReactElement) {
    return render(<SidebarProvider>{component}</SidebarProvider>)
  }

  it('renders dashboard stats when data loads successfully', async () => {
    ;(api.getDashboardStats as jest.Mock).mockResolvedValue({
      success: true,
      data: mockStats,
    })

    const component = await DashboardPage()
    renderWithProvider(component)

    expect(screen.getByText('Total Customers')).toBeInTheDocument()
    expect(screen.getByText('Active Policies')).toBeInTheDocument()
    expect(screen.getByText('Active Claims')).toBeInTheDocument()
  })

  it('renders stat card values', async () => {
    ;(api.getDashboardStats as jest.Mock).mockResolvedValue({
      success: true,
      data: mockStats,
    })

    const component = await DashboardPage()
    renderWithProvider(component)

    expect(screen.getByText('500')).toBeInTheDocument()
    expect(screen.getByText('750')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument()
    expect(screen.getByText('$2,500,000')).toBeInTheDocument()
  })

  it('renders policy type chart', async () => {
    ;(api.getDashboardStats as jest.Mock).mockResolvedValue({
      success: true,
      data: mockStats,
    })

    const component = await DashboardPage()
    renderWithProvider(component)

    expect(screen.getByTestId('policy-type-chart')).toBeInTheDocument()
  })

  it('renders recent claims table', async () => {
    ;(api.getDashboardStats as jest.Mock).mockResolvedValue({
      success: true,
      data: mockStats,
    })

    const component = await DashboardPage()
    renderWithProvider(component)

    expect(screen.getByTestId('recent-claims')).toBeInTheDocument()
  })

  it('handles error when stats fail to load', async () => {
    ;(api.getDashboardStats as jest.Mock).mockResolvedValue({
      success: false,
      data: null,
    })

    const component = await DashboardPage()
    renderWithProvider(component)

    expect(screen.getByText('Error loading dashboard data')).toBeInTheDocument()
  })
})
