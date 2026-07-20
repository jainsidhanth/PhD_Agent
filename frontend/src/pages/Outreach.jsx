import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import {
  CaretDown, FileText, PaperPlaneTilt, XCircle, ClipboardText, Copy, CheckCircle, Sparkle, DownloadSimple,
} from "@phosphor-icons/react";
import { toast } from "sonner";
import { api } from "../api";
import { ScoreBar, TakingBadge, TrackChip } from "../components/Shared";

function Card({ prof, reload }) {
  const [open, setOpen] = useState(false);
  const [brief, setBrief] = useState(prof.brief_md || null);
  const [pkg, setPkg] = useState(null);
  const [busy, setBusy] = useState("");
  const [progress, setProgress] = useState("");

  const doBrief = async () => {
    setBusy("brief");
    try {
      const r = await api.getBrief(prof.id);
      setBrief(r.brief_md);
      toast.success("Brief generated");
    } catch { toast.error("Brief generation failed"); }
    finally { setBusy(""); }
  };

  const doPackage = async () => {
    setBusy("package");
    const done = {};
    try {
      for (const dt of ["cv", "sop", "proposal", "email"]) {
        setProgress(`Generating ${dt.toUpperCase()}...`);
        const r = await api.generateDoc(prof.id, dt);
        done[dt] = r.content;
        if (dt === "email") setPkg({ subject: r.subject, body: r.body, done: { ...done } });
        else setPkg((prev) => ({ ...(prev || {}), done: { ...done } }));
      }
      toast.success("Package generated: CV, SOP, proposal, email");
    } catch { toast.error("Package generation failed (LLM key limit or rate)"); }
    finally { setBusy(""); setProgress(""); }
  };

  const doSend = async () => {
    await api.markSent(prof.id);
    toast.success(`Marked ${prof.name} as sent`);
    reload();
  };

  const doSkip = async () => {
    await api.skip(prof.id);
    toast(`Skipped ${prof.name}`);
    reload();
  };

  const copyEmail = () => {
    if (!pkg) return;
    navigator.clipboard.writeText(`Subject: ${pkg.subject}\n\n${pkg.body}`);
    toast.success("Email copied to clipboard");
  };

  return (
    <div className="bg-white border border-[#E5E0D8] rounded-xl overflow-hidden" data-testid={`outreach-card-${prof.id}`}>
      <button
        onClick={() => setOpen(!open)}
        data-testid={`outreach-toggle-${prof.id}`}
        className="w-full flex items-center gap-4 p-5 text-left hover:bg-[#F8F5F0] transition-colors"
      >
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <span className="font-medium text-[#2A2522]">{prof.name}</span>
            <TrackChip track={prof.best_track} />
            <TakingBadge status={prof.taking_students} />
          </div>
          <div className="text-xs text-[#8A8179] mt-0.5">{prof.university}</div>
        </div>
        <div className="text-right">
          <div className="text-lg font-mono font-semibold text-[#A64B2A]">
            {Math.round((prof.match_score || 0) * 100)}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-[#8A8179]">match</div>
        </div>
        <CaretDown size={20} className={`text-[#8A8179] transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-[#E5E0D8]"
          >
            <div className="p-5 space-y-5">
              <div className="grid sm:grid-cols-2 gap-x-8 gap-y-2 max-w-2xl">
                <ScoreBar label="Research fit" value={prof.score_research} />
                <ScoreBar label="Methods overlap" value={prof.score_methods} />
                <ScoreBar label="Lab activity" value={prof.score_lab_activity} />
                <ScoreBar label="Program strength" value={prof.score_program} />
              </div>

              {prof.focus && <p className="text-sm text-[#5C544E] leading-relaxed">{prof.focus}</p>}

              {/* Workflow */}
              <div className="flex flex-wrap gap-3">
                <button
                  data-testid={`generate-brief-btn-${prof.id}`}
                  onClick={doBrief} disabled={busy}
                  className="inline-flex items-center gap-2 bg-[#F8F5F0] text-[#A64B2A] border border-[#A64B2A] hover:bg-[#F0EBE1] transition-colors px-5 py-2 rounded-md font-medium text-sm disabled:opacity-60"
                >
                  {busy === "brief" ? <Sparkle size={16} className="animate-spin" /> : <ClipboardText size={16} />}
                  1. Generate Brief
                </button>
                <button
                  data-testid={`generate-package-btn-${prof.id}`}
                  onClick={doPackage} disabled={busy}
                  className="inline-flex items-center gap-2 bg-[#E6A64B] text-[#2A2522] hover:bg-[#D5963E] transition-colors px-5 py-2 rounded-md font-medium text-sm disabled:opacity-60"
                >
                  {busy === "package" ? <Sparkle size={16} className="animate-spin" /> : <FileText size={16} />}
                  2. Generate Package
                </button>
                {progress && <span className="self-center text-xs text-[#8A8179]">{progress}</span>}
              </div>

              {brief && (
                <div className="bg-[#FDFCFB] border border-[#E5E0D8] rounded-lg p-5 prose-brief" data-testid={`brief-content-${prof.id}`}>
                  <ReactMarkdown>{brief}</ReactMarkdown>
                </div>
              )}

              {pkg && (
                <div className="space-y-3" data-testid={`package-content-${prof.id}`}>
                  <div className="flex gap-2 flex-wrap">
                    {["cv", "sop", "proposal"].map((k) => (
                      pkg.done && pkg.done[k] ? (
                        <a
                          key={k}
                          href={api.downloadUrl(prof.id, k)}
                          data-testid={`download-${k}-${prof.id}`}
                          className="inline-flex items-center gap-1.5 text-xs px-3 py-1 rounded-full bg-[#6FA3A6]/10 text-[#4d7a7c] border border-[#6FA3A6]/30 hover:bg-[#6FA3A6]/20 transition-colors"
                        >
                          <DownloadSimple size={14} weight="bold" /> {k.toUpperCase()}.docx
                        </a>
                      ) : null
                    ))}
                  </div>
                  {pkg.subject !== undefined && (
                  <>
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold tracking-[0.1em] uppercase text-[#6FA3A6]">Outreach email</label>
                    <button onClick={copyEmail} data-testid={`copy-email-btn-${prof.id}`}
                      className="inline-flex items-center gap-1.5 text-sm text-[#A64B2A] hover:underline">
                      <Copy size={15} /> Copy
                    </button>
                  </div>
                  <textarea
                    data-testid={`email-textarea-${prof.id}`}
                    readOnly
                    value={`Subject: ${pkg.subject}\n\n${pkg.body}`}
                    className="w-full h-64 bg-[#FDFCFB] border border-[#E5E0D8] rounded-md p-4 text-sm font-mono text-[#2A2522] focus:outline-none focus:ring-2 focus:ring-[#6FA3A6]/50 resize-y"
                  />
                  </>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-2 border-t border-[#E5E0D8]">
                <button
                  data-testid={`mark-sent-btn-${prof.id}`}
                  onClick={doSend}
                  className="inline-flex items-center gap-2 bg-[#A64B2A] text-white hover:bg-[#8A3E22] transition-colors px-5 py-2 rounded-md font-medium text-sm"
                >
                  <PaperPlaneTilt size={16} weight="fill" /> Mark as Sent
                </button>
                <button
                  data-testid={`skip-btn-${prof.id}`}
                  onClick={doSkip}
                  className="inline-flex items-center gap-2 text-[#5C544E] hover:text-[#C62828] hover:bg-[#F8F5F0] transition-colors px-4 py-2 rounded-md text-sm"
                >
                  <XCircle size={16} /> Skip
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Outreach({ pending, reload }) {
  return (
    <div className="fade-up space-y-4">
      {pending.length === 0 ? (
        <div className="text-center py-24">
          <PaperPlaneTilt size={56} className="mx-auto text-[#6FA3A6] mb-4" />
          <h3 className="font-serif-display text-2xl text-[#A64B2A]">Nothing pending</h3>
          <p className="text-[#8A8179] mt-1">Discover professors first, then prepare outreach here.</p>
        </div>
      ) : (
        pending.map((p) => <Card key={p.id} prof={p} reload={reload} />)
      )}
    </div>
  );
}
