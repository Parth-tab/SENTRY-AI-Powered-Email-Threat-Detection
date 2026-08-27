import React, { useState, useEffect } from "react";
import { Header } from "./components/layout/Header";
import { Sidebar, NavTab } from "./components/layout/Sidebar";
import { StatCards } from "./components/layout/StatCards";
import { IngestionDropzone } from "./components/dashboard/IngestionDropzone";
import { LiveThreatFeed } from "./components/dashboard/LiveThreatFeed";
import { EmailDetailModal } from "./components/email-detail/EmailDetailModal";
import { OriginRelayMap } from "./components/map/OriginRelayMap";
import { CampaignNetworkGraph } from "./components/graph/CampaignNetworkGraph";
import { ForensicReportView } from "./components/report/ForensicReportView";
import { useWebSocket } from "./hooks/useWebSocket";
import {
  fetchStats,
  fetchEmails,
  fetchEmailDetails,
  seedSampleScenarios
} from "./services/api";
import { DashboardStats, EmailRecordItem, FullEmailDetail } from "./types";
import { ShieldAlert } from "lucide-react";

export function App() {
  const [activeTab, setActiveTab] = useState<NavTab>("dashboard");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [emails, setEmails] = useState<EmailRecordItem[]>([]);
  const [selectedEmailDetail, setSelectedEmailDetail] = useState<FullEmailDetail | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [toastAlert, setToastAlert] = useState<any | null>(null);

  const loadData = async () => {
    try {
      const [statsData, emailsData] = await Promise.all([fetchStats(), fetchEmails()]);
      setStats(statsData);
      setEmails(emailsData);

      // Auto-select first email if available
      if (emailsData.length > 0 && !selectedEmailDetail) {
        const detail = await fetchEmailDetails(emailsData[0].id);
        setSelectedEmailDetail(detail);
      }
    } catch (e) {
      console.error("Data load error:", e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // WebSocket Live Updates
  const { isConnected } = useWebSocket(
    (newAlert) => {
      setToastAlert(newAlert);
      setTimeout(() => setToastAlert(null), 6000);
      loadData();
    },
    () => {
      loadData();
    }
  );

  const handleSelectEmail = async (emailId: string) => {
    try {
      const detail = await fetchEmailDetails(emailId);
      setSelectedEmailDetail(detail);
      if (activeTab === "dashboard" || activeTab === "analyzer") {
        setIsModalOpen(true);
      }
    } catch (e) {
      console.error("Failed to load email details:", e);
    }
  };

  const handleEmailIngested = async (emailRes: any) => {
    await loadData();
    if (emailRes?.id) {
      handleSelectEmail(emailRes.id);
    }
  };

  const handleSeedSamples = async () => {
    setIsSeeding(true);
    try {
      await seedSampleScenarios();
      await loadData();
    } catch (e) {
      console.error("Seeding error:", e);
    } finally {
      setIsSeeding(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-zinc-100 flex flex-col font-sans">
      {/* Top Navigation Header */}
      <Header
        isConnected={isConnected}
        onSeedSamples={handleSeedSamples}
        isSeeding={isSeeding}
      />

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tab) => {
            setActiveTab(tab);
            if (tab === "analyzer" && selectedEmailDetail) {
              setIsModalOpen(true);
            }
          }}
          criticalCount={stats?.threat_distribution?.CRITICAL ?? 0}
        />

        {/* Dynamic Center Stage */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Real-time Toast Alert */}
          {toastAlert && (
            <div className="fixed top-20 right-6 z-50 p-4 rounded-xl bg-rose-500/90 text-white shadow-2xl backdrop-blur flex items-start space-x-3 max-w-md animate-bounce">
              <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-bold uppercase font-mono">
                  {toastAlert.severity} THREAT INTERCEPTED
                </div>
                <div className="text-xs mt-0.5">{toastAlert.title}</div>
                <div className="text-[11px] opacity-80 mt-1">{toastAlert.message}</div>
              </div>
            </div>
          )}

          {activeTab === "dashboard" && (
            <div className="space-y-6">
              {/* Stat Metric Gauges */}
              <StatCards stats={stats} />

              {/* Ingestion Sandbox Zone */}
              <IngestionDropzone onEmailIngested={handleEmailIngested} />

              {/* Real-Time Live Threat Queue */}
              <LiveThreatFeed
                emails={emails}
                onSelectEmail={handleSelectEmail}
                selectedEmailId={selectedEmailDetail?.email?.id}
              />
            </div>
          )}

          {activeTab === "analyzer" && (
            <div className="space-y-6">
              <LiveThreatFeed
                emails={emails}
                onSelectEmail={handleSelectEmail}
                selectedEmailId={selectedEmailDetail?.email?.id}
              />
            </div>
          )}

          {activeTab === "map" && (
            <OriginRelayMap emailDetail={selectedEmailDetail} />
          )}

          {activeTab === "graph" && (
            <CampaignNetworkGraph />
          )}

          {activeTab === "reports" && (
            <ForensicReportView
              emails={emails}
              selectedEmailDetail={selectedEmailDetail}
              onSelectEmail={handleSelectEmail}
            />
          )}
        </main>
      </div>

      {/* Split-Screen Deep Forensic Investigation Modal */}
      {isModalOpen && selectedEmailDetail && (
        <EmailDetailModal
          emailDetail={selectedEmailDetail}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </div>
  );
}

export default App;
