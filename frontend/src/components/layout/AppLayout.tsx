import { useState, useEffect, useCallback, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Search, History, TrendingUp, GitCompareArrows,
  Download, Settings, Menu, ChevronRight,
  Sun, Moon, PanelLeft,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAnalyzeRepo } from '@/lib/hooks'
import { useTheme } from '@/components/ThemeProvider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

interface LayoutProps { children: ReactNode }

const navItems = [
  { section: 'Overview', items: [{ to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }] },
  { section: 'Tools', items: [
    { to: '/analyze', label: 'Analyze', icon: Search },
    { to: '/compare', label: 'Compare', icon: GitCompareArrows },
    { to: '/trends', label: 'Trends', icon: TrendingUp },
  ]},
  { section: 'Data', items: [
    { to: '/history', label: 'Reports', icon: History },
    { to: '/exports', label: 'Exports', icon: Download },
  ]},
]

export function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const analyze = useAnalyzeRepo()
  const { theme, toggleTheme } = useTheme()
  const [searchValue, setSearchValue] = useState('')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [errorDismissed, setErrorDismissed] = useState(false)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchValue.trim()) return
    setErrorDismissed(false)
    analyze.mutate(searchValue, {
      onSuccess: (report) => { setSearchValue(''); navigate(`/report/${report.id}`) },
    })
  }

  useEffect(() => {
    setErrorDismissed(false)
  }, [analyze.isError])

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
      e.preventDefault()
      document.querySelector<HTMLInputElement>('[data-search-input]')?.focus()
    }
  }, [])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  const isActive = (to: string) => location.pathname === to || (to === '/dashboard' && location.pathname === '/')

  const SidebarBody = ({ onNav }: { onNav?: () => void }) => (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center gap-3 border-b border-border px-[20px]">
        <img src="/logo.svg" alt="RepoDoctor Logo" className="h-[32px] w-[32px] shrink-0" />
        {!collapsed && <span className="text-base font-bold tracking-tighter">RepoDoctor</span>}
      </div>
      <nav className="flex-1 overflow-y-auto p-3 space-y-6">
        {navItems.map((section) => (
          <div key={section.section} className="space-y-1">
            {!collapsed && <p className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground/60">{section.section}</p>}
            {section.items.map((item) => {
              const active = isActive(item.to)
              return (
                <Link key={item.to} to={item.to} onClick={onNav} aria-label={item.label}
                  className={cn('flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    active ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground')}>
                  <item.icon size={18} className={cn('shrink-0', active ? 'text-primary' : 'text-muted-foreground')} />
                  {!collapsed && <span>{item.label}</span>}
                  {active && !collapsed && <ChevronRight size={14} className="ml-auto text-muted-foreground" />}
                </Link>
              )
            })}
          </div>
        ))}
        <Separator />
        <div className="space-y-1">
          {!collapsed && <p className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground/60">System</p>}
          <Link to="/settings" onClick={onNav} aria-label="Settings"
            className={cn('flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive('/settings') ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground')}>
            <Settings size={18} className="shrink-0" />
            {!collapsed && <span>Settings</span>}
          </Link>
        </div>
      </nav>
    </div>
  )

  return (
    <TooltipProvider>
      <div className="flex h-screen overflow-hidden bg-background">
        <aside className={cn('hidden flex-col border-r border-border bg-sidebar lg:flex transition-all duration-200', collapsed ? 'w-[68px]' : 'w-[260px]')}>
          <SidebarBody />
        </aside>
        {mobileOpen && (
          <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation menu">
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} aria-hidden="true" />
            <aside className="fixed inset-y-0 left-0 z-50 w-[280px] border-r border-border bg-sidebar shadow-xl">
              <SidebarBody onNav={() => setMobileOpen(false)} />
            </aside>
          </div>
        )}
        <div className="flex flex-1 flex-col overflow-hidden">
          <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border bg-sidebar/80 px-4 backdrop-blur-sm">
            <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-muted-foreground lg:flex"
              aria-label={collapsed ? 'Expand sidebar' : 'Toggle navigation'}
              onClick={() => {
                if (window.innerWidth < 1024) {
                  setMobileOpen(!mobileOpen)
                } else {
                  setCollapsed(!collapsed)
                }
              }}>
              {collapsed ? <PanelLeft size={18} /> : <Menu size={18} />}
            </Button>
            <form onSubmit={handleSearch} className="flex flex-1 items-center gap-2" role="search">
              <div className="relative flex-1">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
                <Input data-search-input type="text" value={searchValue} onChange={(e) => setSearchValue(e.target.value)}
                  placeholder="Analyze a repository..." disabled={analyze.isPending} aria-label="Repository URL"
                  className="h-9 pl-9 bg-muted/50 border-transparent focus:border-border" />
              </div>
              <Tooltip>
                <TooltipTrigger render={<Button variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-muted-foreground" aria-label="Toggle theme" onClick={toggleTheme} />}>
                  {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                </TooltipTrigger>
                <TooltipContent>{theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}</TooltipContent>
              </Tooltip>
              <Button type="submit" size="sm" className="shrink-0" disabled={analyze.isPending || !searchValue.trim()} aria-label="Analyze repository">
                {analyze.isPending ? 'Analyzing...' : 'Analyze'}
              </Button>
            </form>
            {analyze.isError && !errorDismissed && (
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-destructive hidden md:block">{analyze.error.message}</span>
                <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" aria-label="Dismiss error" onClick={() => setErrorDismissed(true)}>
                  <span className="text-lg leading-none">&times;</span>
                </Button>
              </div>
            )}
          </header>
          <main className="flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-[1400px] p-6">{children}</div>
          </main>
        </div>
      </div>
    </TooltipProvider>
  )
}
