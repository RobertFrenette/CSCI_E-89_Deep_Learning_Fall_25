import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Users,
  FileText,
  AlertCircle,
  DollarSign,
  Shield,
} from "lucide-react";
import { PolicyTypeChart } from "@/components/policy-type-chart";
import { RecentClaims } from "@/components/recent-claims";
import { SidebarTrigger } from "@/components/ui/sidebar";

function formatCurrency(value: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export default async function DashboardPage() {
  const response = await api.getDashboardStats();
  const stats = response.data;

  if (!stats) {
    return <div>Error loading dashboard data</div>;
  }

  const statCards = [
    {
      title: "Total Customers",
      value: stats.overview.total_customers,
      icon: Users,
      description: "Registered insureds",
      iconColor: "text-blue-600",
    },
    {
      title: "Active Policies",
      value: stats.overview.active_policies,
      icon: FileText,
      description: `${stats.overview.total_policies} total policies`,
      iconColor: "text-green-600",
    },
    {
      title: "Active Claims",
      value: stats.overview.active_claims,
      icon: AlertCircle,
      description: `${stats.overview.total_claims} total claims`,
      iconColor: "text-orange-600",
    },
    {
      title: "Total Premium Value",
      value: formatCurrency(stats.overview.total_premium_value),
      icon: DollarSign,
      description: "Annual premium revenue",
      iconColor: "text-emerald-600",
    },
  ];

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SidebarTrigger />
          <div>
            <h1 className="text-3xl font-bold">Agent Support Dashboard</h1>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.iconColor}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Policies by Type</CardTitle>
            <CardDescription>Distribution of insurance policies</CardDescription>
          </CardHeader>
          <CardContent>
            <PolicyTypeChart data={stats.policyByType} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI System Types</CardTitle>
            <CardDescription>Coverage by AI system classification</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.aiSystemTypes.map((item, index) => {
                const riskScore = Number(item.avg_risk_score);
                const riskColor = riskScore >= 70 ? "text-red-600" : riskScore >= 50 ? "text-orange-600" : "text-green-600";
                const chartColor = `hsl(var(--chart-${(index % 5) + 1}))`;
                
                return (
                  <div key={item.ai_system_type} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4" style={{ color: chartColor }} />
                        <span className="font-medium">{item.ai_system_type}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-muted-foreground">{item.count} policies</span>
                        <span className={`text-sm font-medium ${riskColor}`}>
                          Risk: {riskScore.toFixed(1)}
                        </span>
                      </div>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="h-2 rounded-full transition-all"
                        style={{ 
                          width: `${Math.min(100, (riskScore / 100) * 100)}%`,
                          backgroundColor: chartColor
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Claims */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Claims</CardTitle>
          <CardDescription>Latest insurance claims activity</CardDescription>
        </CardHeader>
        <CardContent>
          <RecentClaims claims={stats.recentClaims} />
        </CardContent>
      </Card>
    </div>
  );
}
