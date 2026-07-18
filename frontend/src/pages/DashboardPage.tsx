import { useMemo, useState, useCallback } from "react";
import { useReports, useHealth } from "@/lib/hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  ChartContainer,
  ChartTooltip,
  type ChartConfig,
} from "@/components/ui/chart";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Cell } from "recharts";
import { BarChart3, Activity, Clock, AlertTriangle, X } from "lucide-react";
import { Link } from "react-router-dom";

const REPO_COLORS = [
  "oklch(0.65 0.19 264)",
  "oklch(0.72 0.22 149)",
  "oklch(0.62 0.26 304)",
  "oklch(0.75 0.18 55)",
  "oklch(0.63 0.24 15)",
  "oklch(0.70 0.17 200)",
  "oklch(0.68 0.20 330)",
  "oklch(0.73 0.15 100)",
];

const GRADE_COLORS: Record<string, string> = {
  A: "oklch(0.72 0.22 149)",
  B: "oklch(0.65 0.19 264)",
  C: "oklch(0.75 0.18 55)",
  D: "oklch(0.70 0.18 45)",
  F: "oklch(0.58 0.25 27)",
};

function getGradeColor(grade: string): string {
  return GRADE_COLORS[grade] ?? "oklch(0.55 0.01 285)";
}

function getGradeFromScore(score: number): string {
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 60) return "D";
  return "F";
}

function getRepoColor(index: number): string {
  return REPO_COLORS[index % REPO_COLORS.length];
}

export default function DashboardPage() {
  const reports = useReports();
  const health = useHealth();
  const allItems = reports.data?.reports ?? [];

  const [hiddenIds, setHiddenIds] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("rd-hidden-reports") ?? "[]");
    } catch {
      return [];
    }
  });
  const [confirmOpen, setConfirmOpen] = useState(false);

  const updateHidden = useCallback((updater: (prev: string[]) => string[]) => {
    setHiddenIds((prev) => {
      const next = updater(prev);
      localStorage.setItem("rd-hidden-reports", JSON.stringify(next));
      return next;
    });
  }, []);

  const hideReport = useCallback(
    (id: string) => updateHidden((prev) => [...prev, id]),
    [updateHidden],
  );
  const clearAll = useCallback(() => {
    updateHidden((prev) => [
      ...new Set([...prev, ...allItems.slice(0, 5).map((r) => r.id)]),
    ]);
    setConfirmOpen(false);
  }, [updateHidden, allItems]);

  const items = useMemo(
    () => allItems.filter((r) => !hiddenIds.includes(r.id)),
    [allItems, hiddenIds],
  );

  const repoColors = useMemo(() => {
    const names = [...new Set(allItems.map((r) => r.repo_name))].sort();
    return new Map(names.map((name, i) => [name, getRepoColor(i)]));
  }, [allItems]);

  const latestByRepo = useMemo(() => {
    const map = new Map<string, (typeof allItems)[0]>();
    for (const item of allItems) {
      const existing = map.get(item.repo_name);
      if (
        !existing ||
        new Date(item.created_at) > new Date(existing.created_at)
      ) {
        map.set(item.repo_name, item);
      }
    }
    return Array.from(map.values()).sort((a, b) => b.score - a.score);
  }, [allItems]);

  const avgScore =
    allItems.length > 0
      ? Math.round(allItems.reduce((a, r) => a + r.score, 0) / allItems.length)
      : 0;
  const avgGrade = getGradeFromScore(avgScore);

  const barData = latestByRepo.map((r) => ({
    name: r.repo_name.length > 20 ? r.repo_name.slice(-20) : r.repo_name,
    fullName: r.repo_name,
    score: r.score,
    grade: r.grade,
    fill: repoColors.get(r.repo_name) ?? "oklch(0.55 0.01 285)",
  }));

  const chartBarConfig: ChartConfig = Object.fromEntries(
    latestByRepo.map((r, i) => [
      r.repo_name,
      {
        label: r.repo_name,
        color: repoColors.get(r.repo_name) ?? getRepoColor(i),
      },
    ]),
  );

  if (reports.isError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Overview of your repository analyses
            </p>
          </div>
          <Link to="/analyze">
            <Badge variant="default" className="cursor-pointer">
              New Analysis
            </Badge>
          </Link>
        </div>
        <Card className="bg-card/50">
          <CardContent className="p-12 text-center">
            <AlertTriangle
              size={40}
              className="mx-auto text-destructive/50 mb-4"
            />
            <p className="text-muted-foreground mb-4">Failed to load reports</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => reports.refetch()}
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const stats = [
    {
      label: "Total Reports",
      value: reports.data?.total ?? 0,
      icon: BarChart3,
      color: "text-primary",
    },
    {
      label: "Health",
      value:
        health.data?.status === "healthy"
          ? "Healthy"
          : health.isLoading
            ? "..."
            : "Unknown",
      icon: Activity,
      color:
        health.data?.status === "healthy"
          ? "text-primary"
          : "text-muted-foreground",
    },
    {
      label: "Version",
      value: health.data?.version ?? "—",
      icon: Clock,
      color: "text-muted-foreground",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Overview of your repository analyses
          </p>
        </div>
        <Link to="/analyze">
          <Badge variant="default" className="cursor-pointer">
            New Analysis
          </Badge>
        </Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {reports.isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-[100px] rounded-xl" />
            ))
          : stats.map((s) => (
              <Card key={s.label} className="bg-card/50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                      <s.icon size={18} className={s.color} />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{s.label}</p>
                      <p className="text-xl font-semibold">{s.value}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2 bg-card/50">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">
              Recent Reports
            </CardTitle>
            {!reports.isLoading && items.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs text-muted-foreground hover:text-destructive"
                onClick={() => setConfirmOpen(true)}
              >
                Clear
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {reports.isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 rounded-lg" />
                ))}
              </div>
            ) : items.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No recent reports.
                <br />
                Analyze a repository to see it here.
              </p>
            ) : (
              <div className="space-y-2">
                {items.slice(0, 5).map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center rounded-lg border border-transparent p-3 hover:bg-accent/50 transition-colors group"
                  >
                    <Link
                      to={`/report/${report.id}`}
                      aria-label={`View report for ${report.repo_name}`}
                      className="flex items-center gap-3 min-w-0 flex-1"
                    >
                      <div
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                        style={{
                          backgroundColor: `color-mix(in oklch, ${repoColors.get(report.repo_name) ?? "oklch(0.55 0.01 285)"} 12%, transparent)`,
                        }}
                      >
                        <span
                          className="text-xs font-bold"
                          style={{
                            color:
                              repoColors.get(report.repo_name) ??
                              "oklch(0.55 0.01 285)",
                          }}
                        >
                          {report.score}
                        </span>
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">
                          {report.repo_name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {report.grade} —{" "}
                          {new Date(report.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </Link>
                    <button
                      onClick={() => hideReport(report.id)}
                      aria-label={`Remove ${report.repo_name} from recent`}
                      className="shrink-0 p-1 rounded-md text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-destructive hover:bg-destructive/10 transition-all"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="bg-card/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Score Summary</CardTitle>
          </CardHeader>
          <CardContent className="h-full">
            <div className="flex h-full min-h-[280px] flex-col items-center justify-center text-center">
              <div
                className="text-7xl md:text-8xl lg:text-9xl font-extrabold tracking-tight"
                style={{ color: getGradeColor(avgGrade) }}
              >
                {avgScore || "—"}
              </div>
              <p
                className="text-lg font-semibold mt-1"
                style={{ color: getGradeColor(avgGrade) }}
              >
                Grade {avgGrade}
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                {allItems.length} report{allItems.length !== 1 ? "s" : ""}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {latestByRepo.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="bg-card/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Score by Repository
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer
                config={chartBarConfig}
                className="h-[280px] w-full"
              >
                <BarChart
                  data={barData}
                  margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 10 }}
                    interval={0}
                    angle={-20}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <ChartTooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const d = payload[0]?.payload;
                      return (
                        <div className="rounded-lg border border-border/50 bg-background px-3 py-2 text-xs shadow-xl">
                          <p className="font-medium">{d?.fullName}</p>
                          <p className="mt-1" style={{ color: d?.fill }}>
                            Score: {d?.score} — Grade {d?.grade}
                          </p>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {barData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
              <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 mt-3">
                {latestByRepo.map((r) => (
                  <div
                    key={r.repo_name}
                    className="flex items-center gap-1.5 text-xs text-muted-foreground"
                  >
                    <div
                      className="h-2.5 w-2.5 rounded-sm shrink-0"
                      style={{ backgroundColor: repoColors.get(r.repo_name) }}
                    />
                    <span className="truncate max-w-[140px]">
                      {r.repo_name}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Grade Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 py-2">
                {(["A", "B", "C", "D", "F"] as const).map((grade) => {
                  const count = latestByRepo.filter(
                    (r) => r.grade === grade,
                  ).length;
                  const pct =
                    latestByRepo.length > 0
                      ? Math.round((count / latestByRepo.length) * 100)
                      : 0;
                  if (count === 0 && grade !== "A" && grade !== "B")
                    return null;
                  return (
                    <div key={grade} className="flex items-center gap-3">
                      <div className="w-8 text-center">
                        <span
                          className="text-sm font-bold"
                          style={{ color: getGradeColor(grade) }}
                        >
                          {grade}
                        </span>
                      </div>
                      <div className="flex-1 h-5 rounded-full bg-muted/50 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${pct}%`,
                            backgroundColor: getGradeColor(grade),
                          }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground w-12 text-right">
                        {count} repo{count !== 1 ? "s" : ""}
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 mt-4 pt-3 border-t border-border/50">
                {latestByRepo.map((r) => (
                  <div
                    key={r.repo_name}
                    className="flex items-center gap-1.5 text-xs text-muted-foreground"
                  >
                    <div
                      className="h-2.5 w-2.5 rounded-sm shrink-0"
                      style={{ backgroundColor: repoColors.get(r.repo_name) }}
                    />
                    <span className="truncate max-w-[140px]">
                      {r.repo_name}
                    </span>
                    <span
                      className="font-mono text-[10px]"
                      style={{ color: getGradeColor(r.grade) }}
                    >
                      {r.grade}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setConfirmOpen(false)}
          />
          <div className="relative z-50 w-full max-w-sm rounded-xl border border-border bg-background p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-semibold">Clear Recent Reports?</h3>
            <p className="text-sm text-muted-foreground">
              This will remove all reports from the Recent Reports list. The
              reports themselves will remain stored and can still be accessed
              from the Reports page.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfirmOpen(false)}
              >
                Cancel
              </Button>
              <Button variant="destructive" size="sm" onClick={clearAll}>
                Clear
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
