import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useReport } from '@/lib/hooks'
import { exportUrl } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import {
  Bar, BarChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer,
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts'
import {
  ArrowLeft, ExternalLink, Download, Lightbulb, AlertTriangle,
  ChevronDown, ChevronRight, Copy, Check, ChevronsUpDown,
  FileCode, FileImage, Table, File, Shield,
} from 'lucide-react'
import { toast } from 'sonner'
import type { CategoryScore, StructuredRuleResult } from '@/lib/types'

const RULES_PER_PAGE = 15

function ScoreRing({ score, size = 100 }: { score: number; size?: number }) {
  const r = (size - 10) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 70 ? 'var(--color-chart-1)' : score >= 40 ? 'var(--color-chart-4)' : 'var(--color-chart-3)'
  return (
    <svg width={size} height={size} className="shrink-0">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--color-muted)" strokeWidth={6} />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={6} strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset} transform={`rotate(-90 ${size/2} ${size/2})`} style={{ transition: 'stroke-dashoffset 0.6s ease' }} />
      <text x={size/2} y={size/2 - 2} textAnchor="middle" className="fill-foreground text-2xl font-bold">{score}</text>
      <text x={size/2} y={size/2 + 12} textAnchor="middle" className="fill-muted-foreground text-[10px]">/ 100</text>
    </svg>
  )
}

function CopyButton({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      toast.success(label ? `${label} copied` : 'Copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error('Failed to copy')
    }
  }
  return (
    <Button variant="ghost" size="icon-sm" onClick={handleCopy} aria-label={label ? `Copy ${label}` : 'Copy'}>
      {copied ? <Check size={12} className="text-primary" /> : <Copy size={12} />}
    </Button>
  )
}

function RuleRow({ detail }: { detail: StructuredRuleResult }) {
  const [expanded, setExpanded] = useState(false)
  const pass = detail.status === 'PASS'
  return (
    <div className={`group border-b border-border/50 last:border-b-0 transition-colors ${expanded ? 'bg-accent/30' : 'hover:bg-accent/20'}`}>
      <button
        type="button"
        className="flex w-full items-center gap-3 px-4 py-2.5 text-left"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        {expanded ? <ChevronDown size={14} className="shrink-0 text-muted-foreground" /> : <ChevronRight size={14} className="shrink-0 text-muted-foreground" />}
        <Badge variant={pass ? 'default' : 'destructive'} className="text-[10px] shrink-0 w-[44px] justify-center">{detail.status}</Badge>
        <span className="text-sm font-medium shrink-0 w-[140px] truncate" title={detail.rule}>{detail.rule}</span>
        <span className={`text-xs font-mono shrink-0 ${pass ? 'text-primary' : 'text-muted-foreground'}`}>
          {detail.points ?? 0}/{detail.max_points ?? 0}
        </span>
        <span className="text-xs text-muted-foreground flex-1 min-w-0 truncate hidden sm:block" title={detail.evidence}>{detail.evidence}</span>
        <div className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-0.5">
          <CopyButton text={detail.evidence} label="Evidence" />
        </div>
      </button>
      {expanded && (
        <div className="px-4 pb-3 pl-[42px] space-y-2">
          <div className="rounded-lg bg-muted/50 p-3 space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-xs font-medium text-muted-foreground shrink-0 w-16">Evidence:</span>
              <p className="text-xs text-foreground flex-1">{detail.evidence}</p>
            </div>
            {detail.recommendation && (
              <div className="flex items-start gap-2">
                <span className="text-xs font-medium text-muted-foreground shrink-0 w-16">Fix:</span>
                <p className="text-xs text-foreground flex-1">{detail.recommendation}</p>
              </div>
            )}
            <div className="flex items-center gap-2 pt-1">
              <Badge variant="outline" className="text-[10px]">{detail.severity}</Badge>
              {detail.documentation && (
                <a href={detail.documentation} target="_blank" rel="noopener noreferrer" className="text-[10px] text-primary hover:underline">
                  Docs
                </a>
              )}
            </div>
          </div>
          {detail.recommendation && (
            <div className="flex items-center gap-1">
              <CopyButton text={detail.recommendation} label="Recommendation" />
              <span className="text-[10px] text-muted-foreground">Copy recommendation</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function LazyRules({ details }: { details: StructuredRuleResult[] }) {
  const [visibleCount, setVisibleCount] = useState(RULES_PER_PAGE)
  const sentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleCount((prev) => Math.min(prev + RULES_PER_PAGE, details.length))
        }
      },
      { rootMargin: '200px' },
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [details.length])

  useEffect(() => {
    setVisibleCount(RULES_PER_PAGE)
  }, [details.length])

  const visible = details.slice(0, visibleCount)

  return (
    <>
      {visible.map((d, i) => <RuleRow key={`${d.rule}-${i}`} detail={d} />)}
      {visibleCount < details.length && (
        <div ref={sentinelRef} className="px-4 py-2 text-center">
          <Button variant="ghost" size="sm" onClick={() => setVisibleCount((prev) => Math.min(prev + RULES_PER_PAGE, details.length))}>
            Show {Math.min(RULES_PER_PAGE, details.length - visibleCount)} more rules ({details.length - visibleCount} remaining)
          </Button>
        </div>
      )}
    </>
  )
}

function CollapsibleCategory({
  category,
  expanded,
  onToggle,
}: {
  category: CategoryScore
  expanded: boolean
  onToggle: () => void
}) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState<number | 'auto'>(expanded ? 'auto' : 0)

  useEffect(() => {
    if (!contentRef.current) return
    if (expanded) {
      setHeight(contentRef.current.scrollHeight)
      const timer = setTimeout(() => setHeight('auto'), 200)
      return () => clearTimeout(timer)
    } else {
      setHeight(contentRef.current.scrollHeight)
      requestAnimationFrame(() => setHeight(0))
    }
  }, [expanded])

  const pct = Math.round(category.score / category.max_score * 100)
  const passed = category.details?.filter(d => d.status === 'PASS').length ?? 0
  const total = category.details?.length ?? 0
  const failed = total - passed

  return (
    <div className="border border-border/50 rounded-lg overflow-hidden">
      <button
        type="button"
        className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-accent/30 transition-colors"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        {expanded ? <ChevronDown size={16} className="shrink-0 text-muted-foreground" /> : <ChevronRight size={16} className="shrink-0 text-muted-foreground" />}
        <span className="text-sm font-medium flex-1">{category.name}</span>
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs text-muted-foreground">{passed}/{total} passed</span>
          <span className={`text-sm font-bold ${pct >= 70 ? 'text-primary' : pct >= 40 ? 'text-yellow-500' : 'text-destructive'}`}>{pct}%</span>
          <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
            <div className="h-full rounded-full transition-all duration-300" style={{ width: `${pct}%`, backgroundColor: pct >= 70 ? 'var(--color-chart-1)' : pct >= 40 ? 'var(--color-chart-4)' : 'var(--color-chart-3)' }} />
          </div>
          {failed > 0 && <Badge variant="destructive" className="text-[10px]">{failed} fail</Badge>}
        </div>
      </button>
      <div
        ref={contentRef}
        className="overflow-hidden transition-[max-height] duration-200 ease-in-out"
        style={{ maxHeight: height === 'auto' ? 'none' : `${height}px` }}
      >
        <div className="border-t border-border/50">
          {category.details && category.details.length > 0 ? (
            <LazyRules details={category.details} />
          ) : (
            <p className="px-4 py-3 text-xs text-muted-foreground">No detailed results.</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ReportPage() {
  const { id } = useParams<{ id: string }>()
  const report = useReport(id ?? '')
  const r = report.data
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (r && expandedCategories.size === 0) {
      setExpandedCategories(new Set([r.categories[0]?.name].filter(Boolean)))
    }
  }, [r])

  const toggleCategory = useCallback((name: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }, [])

  const expandAll = useCallback(() => {
    if (!r) return
    setExpandedCategories(new Set(r.categories.map(c => c.name)))
  }, [r])

  const collapseAll = useCallback(() => {
    setExpandedCategories(new Set())
  }, [])

  const allExpanded = r != null && r.categories.length > 0 && r.categories.every(c => expandedCategories.has(c.name))

  if (report.isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4"><Skeleton className="h-10 w-10 rounded-lg" /><Skeleton className="h-6 w-48" /></div>
        <div className="grid gap-4 lg:grid-cols-4"><Skeleton className="h-[100px] rounded-xl lg:col-span-1" /><Skeleton className="h-[100px] rounded-xl lg:col-span-3" /></div>
        <Skeleton className="h-[300px] rounded-xl" />
      </div>
    )
  }

  if (report.isError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link to="/history"><Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Back to history"><ArrowLeft size={18} /></Button></Link>
        </div>
        <Card className="bg-card/50">
          <CardContent className="p-12 text-center">
            <AlertTriangle size={40} className="mx-auto text-destructive/50 mb-4" />
            <h2 className="text-lg font-semibold mb-2">Report not found</h2>
            <p className="text-sm text-muted-foreground mb-4">{report.error.message}</p>
            <Button variant="outline" size="sm" onClick={() => report.refetch()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!r) return <p className="text-muted-foreground text-center py-12">Report not found.</p>

  const barData = r.categories.map(c => ({
    name: c.name,
    score: c.score,
    max: c.max_score,
  }))
  const radarData = r.categories.map(c => ({ subject: c.name, score: Math.round(c.score / c.max_score * 100), fullMark: 100 }))

  const chartConfig = { score: { label: 'Score', color: 'var(--color-chart-1)' } } satisfies ChartConfig
  const totalPassed = r.categories.reduce((acc, c) => acc + (c.details?.filter(d => d.status === 'PASS').length ?? 0), 0)
  const totalRules = r.categories.reduce((acc, c) => acc + (c.details?.length ?? 0), 0)

  return (
    <div className="space-y-8">
        <div id="overview" className="space-y-6 scroll-mt-4">
          <div className="flex items-center gap-4">
            <Link to="/history" aria-label="Back to history" className="lg:hidden"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft size={18} /></Button></Link>
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-semibold truncate">{r.repo_name}</h1>
              <p className="text-sm text-muted-foreground">{r.owner} — {new Date(r.created_at).toLocaleString()}</p>
            </div>
            <a href={r.repo_url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${r.repo_name} on GitHub`}>
              <Button variant="outline" size="sm"><ExternalLink size={14} className="mr-2" />GitHub</Button>
            </a>
            <Badge variant="outline" className="text-base px-3 py-1">{r.grade}</Badge>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="flex flex-col items-center justify-center py-4 bg-card/50">
              <ScoreRing score={r.score} />
              <p className="text-sm font-medium mt-1">{r.grade}</p>
            </Card>
            {r.categories.map(c => {
              const pct = Math.round(c.score / c.max_score * 100)
              return (
                <Card key={c.name} className="bg-card/50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-muted-foreground">{c.name}</span>
                      <span className={`text-sm font-bold ${pct >= 70 ? 'text-primary' : pct >= 40 ? 'text-yellow-500' : 'text-destructive'}`}>{pct}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: pct >= 70 ? 'var(--color-chart-1)' : pct >= 40 ? 'var(--color-chart-4)' : 'var(--color-chart-3)' }} />
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1.5">{c.score}/{c.max_score} pts · {c.details?.filter(d => d.status === 'PASS').length ?? 0}/{c.details?.length ?? 0} rules</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          <Card className="bg-card/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Download size={14} className="text-muted-foreground" />
                  <span className="text-sm font-medium">Export Report</span>
                </div>
                <span className="text-xs text-muted-foreground">{totalPassed}/{totalRules} rules passed</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">Download reports in multiple formats</p>
              <div className="flex flex-wrap gap-2">
                {([
                  { key: 'md' as const, label: 'Markdown', icon: FileCode },
                  { key: 'html' as const, label: 'HTML', icon: FileImage },
                  { key: 'csv' as const, label: 'CSV', icon: Table },
                  { key: 'pdf' as const, label: 'PDF', icon: File },
                  { key: 'sarif' as const, label: 'SARIF', icon: Shield },
                ]).map(f => (
                  <a key={f.key} href={exportUrl(r.id, f.key)} target="_blank" rel="noopener noreferrer" aria-label={`Export as ${f.label}`} className="flex-1 min-w-[90px]">
                    <Button variant="outline" size="sm" className="w-full gap-2">
                      <f.icon size={14} className="text-muted-foreground" />
                      {f.label}
                    </Button>
                  </a>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div id="charts" className="space-y-4 scroll-mt-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Score Overview</h2>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="bg-card/50">
              <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Category Scores</CardTitle></CardHeader>
              <CardContent>
                <ChartContainer config={chartConfig} className="h-[220px] w-full">
                  <BarChart data={barData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]} fill="var(--color-chart-1)" />
                  </BarChart>
                </ChartContainer>
              </CardContent>
            </Card>
            <Card className="bg-card/50">
              <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Score Radar</CardTitle></CardHeader>
              <CardContent>
                <div className="flex justify-center">
                  <ResponsiveContainer width="100%" height={220}>
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} />
                      <Radar name="Score" dataKey="score" stroke="var(--color-chart-1)" fill="var(--color-chart-1)" fillOpacity={0.2} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div id="rule-breakdown" className="space-y-4 scroll-mt-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Rule Breakdown</h2>
            <Button variant="ghost" size="sm" onClick={allExpanded ? collapseAll : expandAll} aria-label={allExpanded ? 'Collapse all categories' : 'Expand all categories'}>
              <ChevronsUpDown size={14} className="mr-1" />
              {allExpanded ? 'Collapse All' : 'Expand All'}
            </Button>
          </div>
          <div className="space-y-2">
            {r.categories.map(cat => (
              <div key={cat.name} id={`cat-${cat.name}`} className="scroll-mt-4">
                <CollapsibleCategory
                  category={cat}
                  expanded={expandedCategories.has(cat.name)}
                  onToggle={() => toggleCategory(cat.name)}
                />
              </div>
            ))}
          </div>
        </div>

        <div id="recommendations" className="space-y-4 scroll-mt-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Recommendations ({r.recommendations.length})</h2>
          {r.recommendations.length === 0 ? (
            <Card className="bg-card/50"><CardContent className="p-8 text-center text-muted-foreground">All checks passed — no recommendations.</CardContent></Card>
          ) : (
            <div className="space-y-2">
              {r.recommendations.map((rec, i) => (
                <Card key={i} className="bg-card/50 hover:bg-accent/30 transition-colors">
                  <CardContent className="p-3 flex items-start gap-3">
                    <Lightbulb size={14} className="text-yellow-500 mt-0.5 shrink-0" />
                    <p className="text-sm flex-1">{rec}</p>
                    <CopyButton text={rec} label="Recommendation" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
    </div>
  )
}
