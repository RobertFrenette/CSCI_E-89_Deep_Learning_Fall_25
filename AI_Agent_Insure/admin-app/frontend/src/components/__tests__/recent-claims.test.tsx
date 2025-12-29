import { render, screen } from '@testing-library/react'
import { RecentClaims } from '@/components/recent-claims'

describe('RecentClaims', () => {
  const mockClaims = [
    {
      claim_id: 'CLM-001',
      claim_date: '2024-01-15T00:00:00Z',
      claim_type: 'Auto',
      claim_status: 'Open',
      claim_amount: '5000',
      company_name: 'Acme Corp',
      policy_type: 'Auto Insurance',
    },
    {
      claim_id: 'CLM-002',
      claim_date: '2024-01-10T00:00:00Z',
      claim_type: 'Home',
      claim_status: 'Closed',
      claim_amount: '15000',
      company_name: null,
      policy_type: 'Home Insurance',
    },
  ]

  it('renders without crashing', () => {
    render(<RecentClaims claims={mockClaims} />)
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('renders table headers', () => {
    render(<RecentClaims claims={mockClaims} />)
    expect(screen.getByText('Claim ID')).toBeInTheDocument()
    expect(screen.getByText('Date')).toBeInTheDocument()
    expect(screen.getByText('Type')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Amount')).toBeInTheDocument()
    expect(screen.getByText('Company')).toBeInTheDocument()
  })

  it('renders claim data', () => {
    render(<RecentClaims claims={mockClaims} />)
    expect(screen.getByText('CLM-001')).toBeInTheDocument()
    expect(screen.getByText('CLM-002')).toBeInTheDocument()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('formats currency correctly', () => {
    render(<RecentClaims claims={mockClaims} />)
    expect(screen.getByText('$5,000')).toBeInTheDocument()
    expect(screen.getByText('$15,000')).toBeInTheDocument()
  })

  it('renders status badges', () => {
    render(<RecentClaims claims={mockClaims} />)
    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(screen.getByText('Closed')).toBeInTheDocument()
  })

  it('handles null company name', () => {
    render(<RecentClaims claims={mockClaims} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('handles empty claims array', () => {
    render(<RecentClaims claims={[]} />)
    expect(screen.getByRole('table')).toBeInTheDocument()
  })
})
