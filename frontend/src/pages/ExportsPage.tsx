import { useReports } from '@/lib/hooks'
import { exportUrl } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Download, FileText, AlertTriangle, FileCode, FileImage, Table, File, Shield } from 'lucide-react'

const formats = [
  { key: 'md' as const, label: 'Markdown', desc: 'Plain text report', icon: FileCode },
  { key: 'html' as const, label: 'HTML', desc: 'Formatted web report', icon: FileImage },
  { key: 'csv' as const, label: 'CSV', desc: 'Spreadsheet data', icon: Table },
  { key: 'pdf' as const, label: 'PDF', desc: 'Printable document', icon: File },
  { key: 'sarif' as const, label: 'SARIF', desc: 'Static analysis format', icon: Shield },
]

export default function ExportsPage() {
  const reports = useReports()
  const items = reports.data?.reports ?? []

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-semibold tracking-tight">Exports</h1><p className="text-sm text-muted-foreground mt-1">Download your analysis reports in various formats</p></div>
      {reports.isLoading ? <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)}</div> :
        reports.isError ? (
          <Card className="bg-card/50">
            <CardContent className="p-12 text-center">
              <AlertTriangle size={40} className="mx-auto text-destructive/50 mb-4" />
              <p className="text-muted-foreground mb-4">Failed to load reports</p>
              <Button variant="outline" size="sm" onClick={() => reports.refetch()}>Retry</Button>
            </CardContent>
          </Card>
        ) : items.length === 0 ? (
          <Card className="bg-card/50"><CardContent className="p-12 text-center"><Download size={40} className="mx-auto text-muted-foreground/30 mb-4" /><p className="text-muted-foreground">No reports to export yet.</p></CardContent></Card>
        ) : items.map(report => (
          <Card key={report.id} className="bg-card/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText size={16} className="text-muted-foreground" />
                {report.repo_name}
                <Badge variant="outline" className="text-[10px]">{report.grade}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
                {formats.map(f => (
                  <a key={f.key} href={exportUrl(report.id, f.key)} target="_blank" rel="noopener noreferrer" aria-label={`Export ${report.repo_name} as ${f.label}`}>
                    <Button variant="outline" size="sm" className="w-full justify-start gap-2 h-auto py-2.5">
                      <f.icon size={14} className="shrink-0 text-muted-foreground" />
                      <div className="text-left">
                        <div className="text-xs font-medium">{f.label}</div>
                        <div className="text-[10px] text-muted-foreground">{f.desc}</div>
                      </div>
                    </Button>
                  </a>
                ))}
              </div>
            </CardContent>
          </Card>
        ))
      }
    </div>
  )
}
