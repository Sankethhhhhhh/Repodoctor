import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAnalyzeRepo } from '@/lib/hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, ArrowRight, GitBranch, Zap, Shield, AlertCircle, Loader2, X } from 'lucide-react'

const suggestions = [
  { name: 'vercel/next.js', url: 'https://github.com/vercel/next.js' },
  { name: 'facebook/react', url: 'https://github.com/facebook/react' },
  { name: 'microsoft/vscode', url: 'https://github.com/microsoft/vscode' },
  { name: 'denoland/deno', url: 'https://github.com/denoland/deno' },
]

const features = [
  { icon: Shield, title: 'Security Scan', desc: 'Check dependencies and vulnerabilities' },
  { icon: Zap, title: 'Performance', desc: 'Analyze build and bundle efficiency' },
  { icon: GitBranch, title: 'Code Quality', desc: 'Evaluate structure and maintainability' },
]

export default function AnalyzePage() {
  const [url, setUrl] = useState('')
  const analyze = useAnalyzeRepo()
  const navigate = useNavigate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return
    analyze.mutate(url, {
      onSuccess: (report) => { setUrl(''); navigate(`/report/${report.id}`) },
    })
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Analyze Repository</h1>
        <p className="text-muted-foreground">Enter a GitHub repository URL to get a comprehensive quality report</p>
      </div>
      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
              <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://github.com/owner/repo"
                aria-label="GitHub repository URL" className="h-12 pl-11 pr-32 text-base" disabled={analyze.isPending} />
              <Button type="submit" disabled={analyze.isPending || !url.trim()} className="absolute right-2 top-1/2 -translate-y-1/2 h-8 px-4" size="sm" aria-label="Analyze repository">
                {analyze.isPending ? <><Loader2 size={16} className="animate-spin mr-2" />Analyzing...</> : <>Analyze<ArrowRight size={14} className="ml-2" /></>}
              </Button>
            </div>
            {analyze.isError && (
              <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded-lg">
                <AlertCircle size={16} className="shrink-0" />
                <span className="flex-1">{analyze.error.message}</span>
                <Button type="button" variant="ghost" size="icon" className="h-6 w-6 text-destructive shrink-0" aria-label="Dismiss error" onClick={() => analyze.reset()}>
                  <X size={14} />
                </Button>
              </div>
            )}
          </form>
        </CardContent>
      </Card>
      <div className="space-y-3">
        <p className="text-sm font-medium text-muted-foreground">Try a suggestion</p>
        <div className="grid gap-2 sm:grid-cols-2">
          {suggestions.map((s) => (
            <Button key={s.url} variant="outline" className="justify-start h-auto py-3 px-4" aria-label={`Analyze ${s.name}`} onClick={() => setUrl(s.url)}>
              <div className="flex items-center gap-2 text-left"><GitBranch size={14} className="shrink-0 text-muted-foreground" /><span className="text-sm">{s.name}</span></div>
            </Button>
          ))}
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-3 pt-4">
        {features.map((f) => (
          <Card key={f.title} className="text-center bg-card/50">
            <CardContent className="p-5">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 mb-3"><f.icon size={18} className="text-primary" /></div>
              <h3 className="font-medium text-sm">{f.title}</h3>
              <p className="text-xs text-muted-foreground mt-1">{f.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
