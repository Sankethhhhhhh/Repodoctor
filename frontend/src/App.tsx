import { lazy, Suspense, Component, type ReactNode } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { Layout } from '@/components/layout/AppLayout'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Home } from 'lucide-react'
import { Link } from 'react-router-dom'

const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const AnalyzePage = lazy(() => import('@/pages/AnalyzePage'))
const ReportPage = lazy(() => import('@/pages/ReportPage'))
const HistoryPage = lazy(() => import('@/pages/HistoryPage'))
const ComparePage = lazy(() => import('@/pages/ComparePage'))
const TrendsPage = lazy(() => import('@/pages/TrendsPage'))
const ExportsPage = lazy(() => import('@/pages/ExportsPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } },
})

function Loading() {
  return <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-[80px] rounded-xl" />)}</div>
}

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; error: Error | null }> {
  state = { hasError: false, error: null as Error | null }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card className="m-6">
          <CardContent className="p-8 text-center space-y-4">
            <AlertTriangle size={40} className="mx-auto text-destructive" />
            <h2 className="text-lg font-semibold">Something went wrong</h2>
            <p className="text-sm text-muted-foreground">{this.state.error?.message ?? 'An unexpected error occurred'}</p>
            <Button render={<Link to="/dashboard" />} variant="outline" size="sm">Back to Dashboard</Button>
          </CardContent>
        </Card>
      )
    }
    return this.props.children
  }
}

function NotFound() {
  return (
    <Card className="m-6">
      <CardContent className="p-8 text-center space-y-4">
        <h2 className="text-4xl font-bold text-muted-foreground">404</h2>
        <p className="text-sm text-muted-foreground">Page not found</p>
        <Button render={<Link to="/dashboard" />}><Home size={14} className="mr-2" />Back to Dashboard</Button>
      </CardContent>
    </Card>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <ErrorBoundary>
            <Suspense fallback={<Loading />}>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/analyze" element={<AnalyzePage />} />
                <Route path="/report/:id" element={<ReportPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/compare" element={<ComparePage />} />
                <Route path="/trends" element={<TrendsPage />} />
                <Route path="/exports" element={<ExportsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </Layout>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  )
}
