import { useState } from "react";
import { useReports, useCompare } from "@/lib/hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Bar, BarChart, XAxis, YAxis, CartesianGrid } from "recharts";
import { GitCompareArrows, AlertTriangle } from "lucide-react";

export default function ComparePage() {
  const reports = useReports();
  const items = reports.data?.reports ?? [];
  const [idA, setIdA] = useState("");
  const [idB, setIdB] = useState("");
  const compare = useCompare();

  const chartConfig = {
    scoreA: { label: "Report A", color: "#10b981" },
    scoreB: { label: "Report B", color: "#6366f1" },
  } satisfies ChartConfig;

  const axisTickStyle = {
    fontSize: 11,
    fill: "oklch(0.556 0.014 285.82)" as const,
  };

  const data = compare.data;

  const chartData = data
    ? data.category_comparison.map((c) => ({
        name: c.name,
        scoreA: c.score_a,
        scoreB: c.score_b,
      }))
    : [];

  const sameReport = !!(idA && idB && idA === idB);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Compare Reports
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Select two reports to compare their scores
        </p>
      </div>
      <Card className="bg-card/50">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <div className="flex-1 w-full">
              <label
                className="text-xs text-muted-foreground mb-1 block"
                htmlFor="report-a"
              >
                Report A
              </label>
              <Select value={idA} onValueChange={(v) => setIdA(v ?? "")}>
                <SelectTrigger id="report-a" aria-label="Select first report">
                  <SelectValue placeholder="Select report" />
                </SelectTrigger>
                <SelectContent>
                  {items.map((r) => (
                    <SelectItem key={r.id} value={r.id}>
                      {r.repo_name} — {r.score}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="pt-5 text-muted-foreground">
              <GitCompareArrows size={20} aria-hidden="true" />
            </div>
            <div className="flex-1 w-full">
              <label
                className="text-xs text-muted-foreground mb-1 block"
                htmlFor="report-b"
              >
                Report B
              </label>
              <Select value={idB} onValueChange={(v) => setIdB(v ?? "")}>
                <SelectTrigger id="report-b" aria-label="Select second report">
                  <SelectValue placeholder="Select report" />
                </SelectTrigger>
                <SelectContent>
                  {items.map((r) => (
                    <SelectItem key={r.id} value={r.id}>
                      {r.repo_name} — {r.score}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="pt-5">
              <Button
                onClick={() => {
                  if (idA && idB && !sameReport)
                    compare.mutate({ report_id_a: idA, report_id_b: idB });
                }}
                disabled={!idA || !idB || compare.isPending || sameReport}
                size="sm"
                aria-label="Compare selected reports"
              >
                {compare.isPending ? "Comparing..." : "Compare"}
              </Button>
            </div>
          </div>
          {sameReport && (
            <p className="text-xs text-destructive mt-2 text-center">
              Please select two different reports to compare.
            </p>
          )}
        </CardContent>
      </Card>
      {reports.isLoading ? (
        <Skeleton className="h-[200px] rounded-xl" />
      ) : reports.isError ? (
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
      ) : items.length < 2 ? (
        <p className="text-center text-muted-foreground py-8">
          You need at least 2 reports to compare.
        </p>
      ) : compare.isError ? (
        <p className="text-center text-destructive py-8">
          {compare.error.message}
        </p>
      ) : data ? (
        <div className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="bg-card/50">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{data.report_a.score}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {data.report_a.repo_name}
                </p>
              </CardContent>
            </Card>
            <Card className="bg-card/50">
              <CardContent className="p-4 text-center">
                <Badge
                  variant={
                    data.overall_winner === "Tie" ? "secondary" : "default"
                  }
                  className="text-lg px-4 py-1"
                >
                  {data.overall_winner === "Tie"
                    ? "Tie"
                    : `${data.overall_winner} wins`}
                </Badge>
                <p className="text-sm text-muted-foreground mt-2">
                  Score diff: {data.score_difference}
                </p>
              </CardContent>
            </Card>
            <Card className="bg-card/50">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{data.report_b.score}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {data.report_b.repo_name}
                </p>
              </CardContent>
            </Card>
          </div>
          <Card className="bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Category Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer config={chartConfig} className="h-[250px] w-full">
                <BarChart
                  data={chartData}
                  margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="oklch(0.269 0.006 285.82)"
                  />
                  <XAxis dataKey="name" tick={axisTickStyle} />
                  <YAxis tick={axisTickStyle} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar
                    dataKey="scoreA"
                    name="Report A"
                    fill="var(--color-scoreA)"
                    radius={[3, 3, 0, 0]}
                  />
                  <Bar
                    dataKey="scoreB"
                    name="Report B"
                    fill="var(--color-scoreB)"
                    radius={[3, 3, 0, 0]}
                  />
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>
          {data.improvement_suggestions.length > 0 && (
            <Card className="bg-card/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">
                  Suggestions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.improvement_suggestions.map((s, i) => (
                  <p key={i} className="text-sm text-muted-foreground">
                    {s}
                  </p>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        <p className="text-center text-muted-foreground py-8">
          Select two reports to compare.
        </p>
      )}
    </div>
  );
}
