import { render, screen } from '@testing-library/react'
import { PolicyTypeChart } from '@/components/policy-type-chart'

// Mock Recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Cell: () => <div data-testid="cell" />,
}))

describe('PolicyTypeChart', () => {
  const mockData = [
    {
      policy_type: 'Auto Insurance',
      count: '150',
      total_premium: '250000',
    },
    {
      policy_type: 'Home Insurance',
      count: '120',
      total_premium: '180000',
    },
    {
      policy_type: 'Life Insurance',
      count: '80',
      total_premium: '120000',
    },
  ]

  it('renders without crashing', () => {
    render(<PolicyTypeChart data={mockData} />)
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
  })

  it('renders bar chart component', () => {
    render(<PolicyTypeChart data={mockData} />)
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    expect(screen.getByTestId('bar')).toBeInTheDocument()
  })

  it('renders chart axes', () => {
    render(<PolicyTypeChart data={mockData} />)
    expect(screen.getByTestId('x-axis')).toBeInTheDocument()
    expect(screen.getByTestId('y-axis')).toBeInTheDocument()
  })

  it('renders cartesian grid', () => {
    render(<PolicyTypeChart data={mockData} />)
    expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument()
  })

  it('renders chart without tooltip', () => {
    render(<PolicyTypeChart data={mockData} />)
    // Tooltip was removed - chart should render without it
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  it('handles empty data array', () => {
    render(<PolicyTypeChart data={[]} />)
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })
})
