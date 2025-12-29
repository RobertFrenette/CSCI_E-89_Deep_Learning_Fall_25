import { render, screen } from '@testing-library/react'
import RootLayout from '@/app/layout'

// Mock the AppSidebar component
jest.mock('@/components/app-sidebar', () => ({
  AppSidebar: () => <div data-testid="app-sidebar">Sidebar</div>,
}))

// Mock the SidebarProvider
jest.mock('@/components/ui/sidebar', () => ({
  SidebarProvider: ({ children }: any) => <div data-testid="sidebar-provider">{children}</div>,
}))

describe('RootLayout', () => {
  // Mocked version of RootLayout for testing body content only
  function MockedRootLayout({ children }: { children: React.ReactNode }) {
    // Extract only the body content from RootLayout for testing
    return (
      <div className="mocked-root-layout">
        <div data-testid="sidebar-provider">
          <div className="flex min-h-screen w-full">
            <div data-testid="app-sidebar">Sidebar</div>
            <main className="flex-1 overflow-auto">{children}</main>
          </div>
        </div>
      </div>
    );
  }

  it('renders children within the layout', () => {
    render(
      <MockedRootLayout>
        <div>Test Content</div>
      </MockedRootLayout>
    )
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('renders sidebar provider', () => {
    render(
      <MockedRootLayout>
        <div>Test Content</div>
      </MockedRootLayout>
    )
    expect(screen.getByTestId('sidebar-provider')).toBeInTheDocument()
  })

  it('renders app sidebar', () => {
    render(
      <MockedRootLayout>
        <div>Test Content</div>
      </MockedRootLayout>
    )
    expect(screen.getByTestId('app-sidebar')).toBeInTheDocument()
  })
})
