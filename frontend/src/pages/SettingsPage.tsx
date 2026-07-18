import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Bell, Shield, Database, RefreshCw, Lock } from 'lucide-react'

const settingsSections = [
  { icon: Bell, title: 'Notifications', desc: 'Configure email and webhook notifications for analysis results', status: 'Not configured' },
  { icon: Shield, title: 'API Tokens', desc: 'Manage GitHub personal access tokens for private repositories', status: 'Default' },
  { icon: Database, title: 'Data Retention', desc: 'Set how long to keep analysis reports and exported data', status: '30 days' },
  { icon: RefreshCw, title: 'Auto-Analysis', desc: 'Automatically analyze repositories when new code is pushed', status: 'Enabled' },
]

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Configure your RepoDoctor preferences</p>
      </div>
      <div className="flex items-center gap-2 rounded-lg border border-muted bg-muted/30 px-4 py-2.5 text-sm text-muted-foreground">
        <Lock size={14} className="shrink-0" />
        Settings are currently read-only. Full configuration will be available in a future release.
      </div>
      <Card className="bg-card/50">
        <CardHeader><CardTitle className="text-sm font-medium">Application</CardTitle><CardDescription>General settings for RepoDoctor</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          {settingsSections.map((s, i) => (
            <div key={s.title}>
              {i > 0 && <Separator className="mb-4" />}
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted"><s.icon size={18} className="text-muted-foreground" /></div>
                <div className="flex-1"><p className="text-sm font-medium">{s.title}</p><p className="text-xs text-muted-foreground">{s.desc}</p></div>
                <Badge variant="secondary">{s.status}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
      <Card className="bg-card/50">
        <CardHeader><CardTitle className="text-sm font-medium">About</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-muted-foreground">Version</span><span className="font-medium">1.0.0</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Backend</span><span className="font-medium">FastAPI + PostgreSQL</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Frontend</span><span className="font-medium">React + shadcn/ui</span></div>
        </CardContent>
      </Card>
    </div>
  )
}
