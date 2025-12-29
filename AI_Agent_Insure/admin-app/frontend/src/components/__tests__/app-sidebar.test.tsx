import { render, screen } from '@testing-library/react'
import { AppSidebar } from '@/components/app-sidebar'
import { SidebarProvider } from '@/components/ui/sidebar'

// Mock Next.js Image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />
  },
}))

describe('AppSidebar', () => {
  function renderWithProvider(ui: React.ReactElement) {
    return render(<SidebarProvider>{ui}</SidebarProvider>);
  }

  it('renders without crashing', () => {
    renderWithProvider(<AppSidebar />)
    expect(screen.getByText('AI Agent Insurance')).toBeInTheDocument()
  })

  it('renders company logo and branding', () => {
    renderWithProvider(<AppSidebar />)
    expect(screen.getByText('AI Agent Insurance')).toBeInTheDocument()
    expect(screen.getByText('Admin Portal')).toBeInTheDocument()
    expect(screen.getByAltText('AI Agent Insurance')).toBeInTheDocument()
  })

  it('renders all navigation menu items', () => {
    renderWithProvider(<AppSidebar />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Policies')).toBeInTheDocument()
    expect(screen.getByText('Customers')).toBeInTheDocument()
    expect(screen.getByText('Claims')).toBeInTheDocument()
  })

  it('renders navigation group label', () => {
    renderWithProvider(<AppSidebar />)
    expect(screen.getByText('Navigation')).toBeInTheDocument()
  })

  it('renders links with correct hrefs', () => {
    renderWithProvider(<AppSidebar />)
    expect(screen.getByRole('link', { name: /Dashboard/i })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: /Policies/i })).toHaveAttribute('href', '/policies')
    expect(screen.getByRole('link', { name: /Customers/i })).toHaveAttribute('href', '/customers')
    expect(screen.getByRole('link', { name: /Claims/i })).toHaveAttribute('href', '/claims')
  })
})
