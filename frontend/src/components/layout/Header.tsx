import React from "react";
import { Shield, Radio, Sparkles, RefreshCw } from "lucide-react";

interface HeaderProps {
  isConnected: boolean;
  onSeedSamples: () => void;
  isSeeding: boolean;
}

export const Header: React.FC<HeaderProps> = ({ isConnected, onSeedSamples, isSeeding }) => {
  return (
    <header className="h-16 border-b border-[#27272A] bg-[#121215] px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-rose-500/20 to-red-600/30 border border-rose-500/40 flex items-center justify-center text-rose-400 shadow-lg shadow-rose-500/10">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold tracking-tight text-white text-base">SENTRY</h1>
            <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
              FORENSIC SOC
            </span>
            <span className="text-xs text-zinc-500 hidden md:inline">| PS ID 26106</span>
          </div>
          <p className="text-[11px] text-zinc-400 hidden sm:block">
            Calibrated ML Email Threat Detection, Geolocation & Evidentiary Attribution
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Live WebSocket Telemetry Indicator */}
        <div className="flex items-center space-x-2 px-2.5 py-1 rounded-full bg-[#18181B] border border-[#27272A] text-xs">
          <span className="relative flex h-2 w-2">
            {isConnected ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            )}
          </span>
          <span className="font-mono text-[11px] text-zinc-300">
            {isConnected ? "LIVE STREAM" : "CONNECTING..."}
          </span>
        </div>

        {/* Demo Scenario Seeder */}
        <button
          onClick={onSeedSamples}
          disabled={isSeeding}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-600 border border-zinc-700 text-xs font-medium text-zinc-200 transition-colors shadow-sm disabled:opacity-50"
        >
          {isSeeding ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-rose-400" />
          ) : (
            <Sparkles className="w-3.5 h-3.5 text-rose-400" />
          )}
          <span>{isSeeding ? "Seeding..." : "Load Demo Scenarios"}</span>
        </button>
      </div>
    </header>
  );
};
