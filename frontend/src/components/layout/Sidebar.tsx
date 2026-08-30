import React from "react";
import { LayoutDashboard, MailSearch, Globe2, Network, FileCheck2, ShieldAlert } from "lucide-react";

export type NavTab = "dashboard" | "analyzer" | "map" | "graph" | "reports";

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  criticalCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab, criticalCount }) => {
  const navItems = [
    { id: "dashboard" as NavTab, label: "SOC Dashboard", icon: LayoutDashboard },
    { id: "analyzer" as NavTab, label: "Email Analyzer", icon: MailSearch },
    { id: "map" as NavTab, label: "Relay World Map", icon: Globe2 },
    { id: "graph" as NavTab, label: "Campaign Graph", icon: Network },
    { id: "reports" as NavTab, label: "Forensic Vault", icon: FileCheck2 }
  ];

  return (
    <aside className="w-60 border-r border-[#27272A] bg-[#121215] flex flex-col justify-between p-3 select-none">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[10px] font-mono tracking-wider text-zinc-500 uppercase">
          Forensic Operations
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-rose-500/15 text-rose-400 border border-rose-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 border border-transparent"
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Icon className={`w-4 h-4 ${isActive ? "text-rose-400" : "text-zinc-400"}`} />
                <span>{item.label}</span>
              </div>
              {item.id === "dashboard" && criticalCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold bg-rose-500 text-white">
                  {criticalCount}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="space-y-2">
        <div className="p-3 rounded-lg bg-[#18181B] border border-[#27272A] space-y-1.5">
          <div className="flex items-center space-x-1.5 text-xs text-zinc-300 font-semibold">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            <span>Evidentiary Engine</span>
          </div>
          <p className="text-[11px] text-zinc-500 leading-tight">
            RFC 3227 Immutable Chain-of-Custody & Origin Attribution Active
          </p>
        </div>

        <div className="px-1 text-[10px] text-zinc-500 leading-tight">
          This product includes GeoLite2 data created by MaxMind, available from{" "}
          <a
            href="https://www.maxmind.com"
            target="_blank"
            rel="noreferrer"
            className="text-zinc-400 hover:text-zinc-300 underline"
          >
            https://www.maxmind.com
          </a>.
        </div>
      </div>
    </aside>
  );
};
