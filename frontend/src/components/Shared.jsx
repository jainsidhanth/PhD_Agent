import React from "react";

export const TRACK_LABELS = {
  disorders: "Psychiatric disorders",
  eeg_fmri: "EEG / fMRI",
  attention: "Attention",
  memory_dementia: "Memory & aging",
  parkinsons: "Parkinson's",
  impulse_reward: "Impulse & reward",
  decision_making: "Decision-making",
  multisensory_digital_health: "Multisensory / digital health",
};

export function ScoreBar({ label, value, testid }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="flex items-center gap-3" data-testid={testid}>
      <span className="text-xs w-32 shrink-0 text-[#5C544E] tracking-tight">{label}</span>
      <div className="score-track">
        <div className="score-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono w-9 text-right text-[#2A2522]">{pct}</span>
    </div>
  );
}

export function CompactBar({ value }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="score-track" style={{ maxWidth: 90 }}>
        <div className="score-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono w-7 text-right text-[#5C544E]">{pct}</span>
    </div>
  );
}

export function TakingBadge({ status }) {
  const map = {
    yes: { bg: "#E8F5E9", fg: "#2E7D32", label: "Recruiting" },
    no: { bg: "#FFEBEE", fg: "#C62828", label: "Closed" },
    unknown: { bg: "#F5F5F5", fg: "#616161", label: "Unknown" },
  };
  const s = map[status] || map.unknown;
  return (
    <span
      className="px-2.5 py-0.5 rounded-full text-xs font-medium border"
      style={{ background: s.bg, color: s.fg, borderColor: s.fg + "33" }}
      data-testid={`taking-badge-${status}`}
    >
      {s.label}
    </span>
  );
}

export function TrackChip({ track }) {
  if (!track) return <span className="text-xs text-[#8A8179]">-</span>;
  return (
    <span className="px-2.5 py-0.5 rounded-full text-xs font-medium border border-[#6FA3A6]/40 text-[#4d7a7c] bg-[#6FA3A6]/10">
      {TRACK_LABELS[track] || track}
    </span>
  );
}
