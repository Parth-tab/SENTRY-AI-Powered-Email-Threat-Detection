import React from "react";
import { ShieldAlert, AlertTriangle, CheckCircle2, Network, Activity } from "lucide-react";
import { DashboardStats } from "../../types";

interface StatCardsProps {
  stats: DashboardStats | null;
}

export const StatCards: React.FC<StatCardsProps> = ({ stats }) => {
  const total = stats?.total_emails_analyzed ?? 0;
  const critical = stats?.threat_distribution?.CRITICAL ?? 0;
  const high = stats?.threat_distribution?.HIGH ?? 0;
  const low = stats?.threat_distribution?.LOW ?? 0;
  const campaigns = stats?.active_campaigns_count ?? 0;

  const cards = [
    {
      title: "Total Emails Ingested",
      value: total,
      subtitle: "Multi-protocol RFC 5322 intake",
      icon: Activity,
      textColor: "text-zinc-100",
      borderColor: "border-zinc-800",
      bgColor: "bg-[#18181B]"
    },
    {
      title: "Critical Threats Flagged",
      value: critical,
      subtitle: "Urgent response required",
      icon: ShieldAlert,
      textColor: "text-rose-400",
      borderColor: "border-rose-500/30",
      bgColor: "bg-rose-500/5"
    },
    {
      title: "Suspicious / BEC Risks",
      value: high,
      subtitle: "Impersonation & wire fraud",
      icon: AlertTriangle,
      textColor: "text-amber-400",
      borderColor: "border-amber-500/30",
      bgColor: "bg-amber-500/5"
    },
    {
      title: "Attributed Campaigns",
      value: campaigns,
      subtitle: "Graph-correlated clusters",
      icon: Network,
      textColor: "text-indigo-400",
      borderColor: "border-indigo-500/30",
      bgColor: "bg-indigo-500/5"
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className={`p-4 rounded-xl border ${c.borderColor} ${c.bgColor} shadow-sm flex flex-col justify-between`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-zinc-400">{c.title}</span>
              <Icon className={`w-4 h-4 ${c.textColor}`} />
            </div>
            <div className="mt-3">
              <div className={`text-2xl font-bold font-mono ${c.textColor}`}>{c.value}</div>
              <div className="text-[11px] text-zinc-500 mt-0.5">{c.subtitle}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
