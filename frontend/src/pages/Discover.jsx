import React, { useState } from "react";
import { motion } from "framer-motion";
import { MagnifyingGlass, Sparkle } from "@phosphor-icons/react";
import { toast } from "sonner";
import { api } from "../api";
import { ScoreBar, CompactBar, TakingBadge, TrackChip } from "../components/Shared";

export default function Discover({ professors, tracks, reload }) {
  const [perTrack, setPerTrack] = useState(2);
  const [onlyTrack, setOnlyTrack] = useState("");
  const [loading, setLoading] = useState(false);

  const runDiscover = async () => {
    setLoading(true);
    try {
      const res = await api.discover({ per_track: Number(perTrack), only_track: onlyTrack || null });
      toast.success(`Discovery complete: ${res.created} new professor(s) added`);
      if (res.errors?.length) toast.warning(`${res.errors.length} track(s) had issues`);
      await reload();
    } catch (e) {
      toast.error("Discovery failed. Check your LLM key balance.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-up">
      <div className="bg-white border border-[#E5E0D8] rounded-xl p-6 mb-8">
        <div className="flex flex-wrap items-end gap-6">
          <div>
            <label className="block text-xs font-semibold tracking-[0.1em] uppercase text-[#6FA3A6] mb-2">
              Per track
            </label>
            <select
              data-testid="per-track-select"
              value={perTrack}
              onChange={(e) => setPerTrack(e.target.value)}
              className="bg-[#FDFCFB] border border-[#E5E0D8] rounded-md px-4 py-2 text-[#2A2522] focus:outline-none focus:ring-2 focus:ring-[#6FA3A6]/50"
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold tracking-[0.1em] uppercase text-[#6FA3A6] mb-2">
              Track filter
            </label>
            <select
              data-testid="track-filter-select"
              value={onlyTrack}
              onChange={(e) => setOnlyTrack(e.target.value)}
              className="bg-[#FDFCFB] border border-[#E5E0D8] rounded-md px-4 py-2 text-[#2A2522] min-w-[240px] focus:outline-none focus:ring-2 focus:ring-[#6FA3A6]/50"
            >
              <option value="">All 8 tracks</option>
              {tracks.map((t) => (
                <option key={t.key} value={t.key}>{t.label}</option>
              ))}
            </select>
          </div>
          <button
            data-testid="find-professors-btn"
            onClick={runDiscover}
            disabled={loading}
            className="ml-auto inline-flex items-center gap-2 bg-[#A64B2A] text-white hover:bg-[#8A3E22] transition-colors px-6 py-2.5 rounded-md font-medium shadow-sm disabled:opacity-60"
          >
            {loading ? (
              <><Sparkle size={18} className="animate-spin" /> Searching...</>
            ) : (
              <><MagnifyingGlass size={18} weight="bold" /> Find Professors</>
            )}
          </button>
        </div>
        <p className="text-sm text-[#8A8179] mt-3">
          Uses Claude to surface active PhD supervisors per research track, scored on 4 dimensions.
        </p>
      </div>

      {professors.length === 0 ? (
        <div className="text-center py-24">
          <MagnifyingGlass size={56} className="mx-auto text-[#6FA3A6] mb-4" />
          <h3 className="font-serif-display text-2xl text-[#A64B2A]">No professors yet</h3>
          <p className="text-[#8A8179] mt-1">Run a discovery to build your shortlist.</p>
        </div>
      ) : (
        <div className="bg-white border border-[#E5E0D8] rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="professors-table">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-[#8A8179] border-b border-[#E5E0D8]">
                  <th className="py-3 px-4 font-semibold">Professor</th>
                  <th className="py-3 px-4 font-semibold">Track</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Research</th>
                  <th className="py-3 px-4 font-semibold">Methods</th>
                  <th className="py-3 px-4 font-semibold">Lab</th>
                  <th className="py-3 px-4 font-semibold">Program</th>
                  <th className="py-3 px-4 font-semibold">Overall</th>
                </tr>
              </thead>
              <tbody>
                {professors.map((p, i) => (
                  <motion.tr
                    key={p.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(i * 0.03, 0.4) }}
                    className="border-b border-[#E5E0D8] last:border-0 hover:bg-[#F8F5F0]"
                    data-testid={`professor-row-${p.id}`}
                  >
                    <td className="py-3 px-4">
                      <div className="font-medium text-[#2A2522]">{p.name}</div>
                      <div className="text-xs text-[#8A8179]">{p.university}</div>
                      {p.email && <div className="text-xs font-mono text-[#6FA3A6]">{p.email}</div>}
                    </td>
                    <td className="py-3 px-4"><TrackChip track={p.best_track} /></td>
                    <td className="py-3 px-4"><TakingBadge status={p.taking_students} /></td>
                    <td className="py-3 px-4"><CompactBar value={p.score_research} /></td>
                    <td className="py-3 px-4"><CompactBar value={p.score_methods} /></td>
                    <td className="py-3 px-4"><CompactBar value={p.score_lab_activity} /></td>
                    <td className="py-3 px-4"><CompactBar value={p.score_program} /></td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="score-track" style={{ maxWidth: 90 }}>
                          <div className="score-fill" style={{ width: `${Math.round((p.match_score || 0) * 100)}%` }} />
                        </div>
                        <span className="text-sm font-mono font-semibold text-[#A64B2A] w-8">
                          {Math.round((p.match_score || 0) * 100)}
                        </span>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
