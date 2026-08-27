import React, { useState } from "react";
import { Globe2, ShieldAlert, ShieldCheck, MapPin, ArrowRight, Server, Compass } from "lucide-react";
import { FullEmailDetail, RelayHop } from "../../types";

interface OriginRelayMapProps {
  emailDetail: FullEmailDetail | null;
}

export const OriginRelayMap: React.FC<OriginRelayMapProps> = ({ emailDetail }) => {
  if (!emailDetail) {
    return (
      <div className="p-12 text-center text-zinc-500 bg-[#18181B] border border-[#27272A] rounded-xl">
        <Globe2 className="w-12 h-12 mx-auto mb-3 text-zinc-600 animate-pulse" />
        <h3 className="text-sm font-semibold text-zinc-300">No Email Selected for Origin Tracing</h3>
        <p className="text-xs text-zinc-500 mt-1">Select an email artifact from the dashboard to reconstruct its transmission path.</p>
      </div>
    );
  }

  const { email, analysis } = emailDetail;
  const origin = analysis.origin_assessment;
  const hops = analysis.relay_path || [];
  const [selectedHop, setSelectedHop] = useState<RelayHop | null>(
    hops.find((h) => h.hop_type === "origin") || hops[0] || null
  );

  // SVG Coordinates projection (Mercator approximation for SVG 800x400)
  const projectCoords = (lat: number, lon: number) => {
    const x = ((lon + 180) / 360) * 800;
    const latRad = (lat * Math.PI) / 180;
    const mercN = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
    const y = 200 - (mercN / Math.PI) * 160;
    return { x: Math.max(20, Math.min(780, x)), y: Math.max(20, Math.min(380, y)) };
  };

  const originLat = origin?.geolocation?.latitude || 52.3676;
  const originLon = origin?.geolocation?.longitude || 4.9041;
  const originPt = projectCoords(originLat, originLon);

  // Simulated destination coordinates (e.g. Target Enterprise / User mail server in US/India)
  const destPt = projectCoords(19.0760, 72.8777); // Mumbai
  const intermediatePt = projectCoords(48.8566, 2.3522); // Paris transit

  return (
    <div className="space-y-6">
      {/* Map Card */}
      <div className="p-6 rounded-2xl bg-[#18181B] border border-[#27272A] shadow-lg relative overflow-hidden">
        <div className="flex items-center justify-between pb-4 border-b border-[#27272A] mb-4">
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <Globe2 className="w-4 h-4 text-rose-400" />
              <span>Multi-Hop Received Transmission Path Reconstruction</span>
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Reconstructing exact RFC 5321 relay hops from earliest origin to perimeter mail gateway
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="px-2 py-1 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
              Total Hops: {hops.length}
            </span>
            <span
              className={`px-2 py-1 rounded border font-bold ${
                origin?.anonymization?.tor_exit_node
                  ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                  : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
              }`}
            >
              {origin?.anonymization?.tor_exit_node ? "TOR ANONYMIZED" : "DIRECT ISP"}
            </span>
          </div>
        </div>

        {/* Interactive SVG World Map Canvas */}
        <div className="relative w-full h-80 bg-[#0E0E11] rounded-xl border border-[#27272A] flex items-center justify-center overflow-hidden">
          <svg className="w-full h-full" viewBox="0 0 800 400">
            {/* World Grid Lines */}
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#27272A" strokeWidth="0.5" />
              </pattern>
              <linearGradient id="arcGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#FA7273" />
                <stop offset="50%" stopColor="#F59E0B" />
                <stop offset="100%" stopColor="#10B981" />
              </linearGradient>
            </defs>
            <rect width="800" height="400" fill="url(#grid)" />

            {/* Stylized Continent Outlines (Vector representation) */}
            <path
              d="M150,100 Q180,80 220,120 T260,180 T200,240 T140,160 Z"
              fill="#1F1F24"
              stroke="#2E2E36"
              strokeWidth="0.8"
            />
            <path
              d="M450,90 Q520,70 580,110 T650,150 T600,220 T480,180 Z"
              fill="#1F1F24"
              stroke="#2E2E36"
              strokeWidth="0.8"
            />
            <path
              d="M480,220 Q540,240 560,320 T480,360 T440,280 Z"
              fill="#1F1F24"
              stroke="#2E2E36"
              strokeWidth="0.8"
            />

            {/* Relay Transmission Arc (Origin -> Transit -> Destination) */}
            <path
              d={`M ${originPt.x} ${originPt.y} Q ${(originPt.x + destPt.x) / 2} ${
                Math.min(originPt.y, destPt.y) - 60
              } ${destPt.x} ${destPt.y}`}
              fill="none"
              stroke="url(#arcGrad)"
              strokeWidth="2.5"
              strokeDasharray="6,4"
              className="animate-pulse"
            />

            {/* Origin Node Pin */}
            <g transform={`translate(${originPt.x}, ${originPt.y})`}>
              <circle r="12" fill="#FA7273" opacity="0.25" className="animate-ping" />
              <circle r="6" fill="#FA7273" stroke="#FFFFFF" strokeWidth="1.5" />
              <text x="10" y="-8" fill="#FA7273" fontSize="10" fontFamily="monospace" fontWeight="bold">
                Origin: {origin?.probable_origin_ip} ({origin?.geolocation?.country_code})
              </text>
            </g>

            {/* Destination Node Pin */}
            <g transform={`translate(${destPt.x}, ${destPt.y})`}>
              <circle r="8" fill="#10B981" opacity="0.3" />
              <circle r="5" fill="#10B981" stroke="#FFFFFF" strokeWidth="1.5" />
              <text x="10" y="14" fill="#10B981" fontSize="10" fontFamily="monospace" fontWeight="bold">
                Inbound MX: {email.recipient || "Enterprise Gateway"}
              </text>
            </g>
          </svg>

          {/* Map Floating HUD */}
          <div className="absolute bottom-3 left-3 bg-[#18181B]/90 backdrop-blur border border-[#27272A] p-2.5 rounded-lg text-[11px] font-mono space-y-1">
            <div className="text-zinc-400">
              <span className="text-rose-400 font-bold">● Origin Point:</span>{" "}
              {origin?.geolocation?.city}, {origin?.geolocation?.country} ({originLat.toFixed(2)}, {originLon.toFixed(2)})
            </div>
            <div className="text-zinc-400">
              <span className="text-amber-400 font-bold">● Infrastructure:</span> {origin?.geolocation?.asn} (
              {origin?.geolocation?.isp})
            </div>
          </div>
        </div>

        {/* Hop-by-Hop Chronological Relay List */}
        <div className="mt-6 space-y-3">
          <h3 className="text-xs font-bold text-zinc-200 uppercase tracking-wider font-mono">
            Chronological Hop Chain Breakdown (Earliest to Final Destination)
          </h3>
          <div className="space-y-2">
            {hops.map((hop, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border text-xs font-mono transition-all cursor-pointer ${
                  hop.hop_type === "origin"
                    ? "bg-rose-500/10 border-rose-500/40 text-zinc-200"
                    : "bg-[#121215] border-[#27272A] text-zinc-400 hover:border-zinc-700"
                }`}
                onClick={() => setSelectedHop(hop)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        hop.hop_type === "origin"
                          ? "bg-rose-500 text-white"
                          : "bg-zinc-800 text-zinc-300"
                      }`}
                    >
                      HOP #{hop.hop_number}
                    </span>
                    <span className="font-bold text-zinc-200">
                      {hop.from_ip ? `IP: ${hop.from_ip}` : hop.from_host || "Internal Server"}
                    </span>
                    {hop.hop_type === "origin" && (
                      <span className="text-[10px] text-rose-400 font-bold uppercase">
                        [EARLIEST RELIABLE HOP]
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-zinc-500">{hop.protocol}</span>
                </div>
                <div className="mt-1 text-[11px] text-zinc-400 truncate">
                  <span className="text-zinc-500">By:</span> {hop.by_host || "Local Relay"} |{" "}
                  <span className="text-zinc-500">Time:</span> {hop.timestamp || "N/A"}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
