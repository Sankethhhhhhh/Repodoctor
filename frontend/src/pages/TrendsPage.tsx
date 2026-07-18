import { useReports } from '@/lib/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { Line, LineChart, XAxis, YAxis, CartesianGrid } from 'recharts'
import { TrendingUp, AlertTriangle } from 'lucide-react'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'

export default function TrendsPage() {
  const reports = useReports()
  const items = reports.data?.reports ?? []

  const chartData = useMemo(() => {
    return [...items].reverse().map(r => ({
      date: new Date(r.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      score: r.score,
    }))
  }, [items])

  const chartConfig = {
    score: { label: 'Score', color: 'hsl(var(--chart-1))' },
  } satisfies ChartConfig

  const axisTickStyle = { fontSize: 11, fill: 'oklch(0.556 0.014 285.82)' as const }

  if (reports.isLoading) return <div className="space-y-6"><div><h1 className="text-2xl font-semibold tracking-tight">Score Trends</h1></div><Skeleton className="h-[300px] rounded-xl" /></div>

  if (reports.isError) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-semibold tracking-tight">Score Trends</h1><p className="text-sm text-muted-foreground mt-1">Track how repository quality evolves over time</p></div>
        <Card className="bg-card/50">
          <CardContent className="p-12 text-center">
            <AlertTriangle size={40} className="mx-auto text-destructive/50 mb-4" />
            <p className="text-muted-foreground mb-4">Failed to load reports</p>
            <Button variant="outline" size="sm" onClick={() => reports.refetch()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-semibold tracking-tight">Score Trends</h1><p className="text-sm text-muted-foreground mt-1">Track how repository quality evolves over time</p></div>
      {items.length < 2 ? <Card className="bg-card/50"><CardContent className="p-12 text-center"><TrendingUp size={40} className="mx-auto text-muted-foreground/30 mb-4" /><p className="text-muted-foreground">You need at least 2 reports to see trends.</p></CardContent></Card> :
        <Card className="bg-card/50">
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Score Over Time</CardTitle></CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px] w-full">
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="oklch(0.269 0.006 285.82)" />
                <XAxis dataKey="date" tick={axisTickStyle} />
                <YAxis domain={[0, 100]} tick={axisTickStyle} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line type="monotone" dataKey="score" stroke="var(--color-score)" strokeWidth={2} dot={{ r: 4, fill: 'var(--color-score)', stroke: 'var(--color-score)' }} activeDot={{ r: 6, fill: 'var(--color-score)', stroke: 'oklch(0.985 0.002 247.84)', strokeWidth: 2 }} />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>
      }
      {items.length > 0 && (
        <Card className="bg-card/50">
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">All Reports</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[...items].reverse().map(r => (
                <Link key={r.id} to={`/report/${r.id}`} aria-label={`View report for ${r.repo_name}, score ${r.score}`}
                  className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent/50 transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{r.repo_name}</p>
                    <p className="text-xs text-muted-foreground">{new Date(r.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-lg font-bold ${r.score >= 70 ? 'text-primary' : r.score >= 40 ? 'text-yellow-500' : 'text-destructive'}`}>{r.score}</p>
                    <p className="text-xs text-muted-foreground">{r.grade}</p>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
