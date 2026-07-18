import { useReports } from '@/lib/hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Link } from 'react-router-dom'
import { ArrowRight, Clock, AlertTriangle } from 'lucide-react'

export default function HistoryPage() {
  const reports = useReports()
  const items = reports.data?.reports ?? []

  if (reports.isLoading) return <div className="space-y-4">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 rounded-lg" />)}</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-semibold tracking-tight">Report History</h1><p className="text-sm text-muted-foreground mt-1">{reports.data?.total ?? 0} reports total</p></div>
        <Link to="/analyze"><Button size="sm">New Analysis</Button></Link>
      </div>
      {reports.isError ? (
        <Card className="bg-card/50">
          <CardContent className="p-12 text-center">
            <AlertTriangle size={40} className="mx-auto text-destructive/50 mb-4" />
            <p className="text-muted-foreground mb-4">Failed to load reports</p>
            <Button variant="outline" size="sm" onClick={() => reports.refetch()}>Retry</Button>
          </CardContent>
        </Card>
      ) : items.length === 0 ? (
        <Card className="bg-card/50"><CardContent className="p-12 text-center"><Clock size={40} className="mx-auto text-muted-foreground/30 mb-4" /><p className="text-muted-foreground">No reports yet.</p><Link to="/analyze"><Button variant="link" className="mt-2">Analyze a repository</Button></Link></CardContent></Card>
      ) : (
        <Card className="bg-card/50">
          <Table>
            <TableHeader><TableRow><TableHead>Repository</TableHead><TableHead>Score</TableHead><TableHead>Grade</TableHead><TableHead>Date</TableHead><TableHead /></TableRow></TableHeader>
            <TableBody>
              {items.map((report) => (
                <TableRow key={report.id}>
                  <TableCell className="font-medium">{report.repo_name}</TableCell>
                  <TableCell><span className={`font-semibold ${report.score >= 70 ? 'text-primary' : report.score >= 40 ? 'text-yellow-500' : 'text-destructive'}`}>{report.score}</span></TableCell>
                  <TableCell><Badge variant={report.grade === 'A' ? 'default' : report.grade === 'F' ? 'destructive' : 'secondary'}>{report.grade}</Badge></TableCell>
                  <TableCell className="text-muted-foreground text-sm">{new Date(report.created_at).toLocaleDateString()}</TableCell>
                  <TableCell><Link to={`/report/${report.id}`} aria-label={`View report for ${report.repo_name}`}><Button variant="ghost" size="sm"><ArrowRight size={14} /></Button></Link></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  )
}
