import React, { useState } from "react";
import { motion } from "framer-motion";
import { Plus, ClockCounterClockwise, ArchiveBox } from "@phosphor-icons/react";
import { toast } from "sonner";
import { api } from "../api";
import { TrackChip } from "../components/Shared";

function Toggle({ checked, onChange, label, testid }) {
  return (
    <label className="inline-flex items-center gap-2 cursor-pointer select-none" data-testid={testid}>
      <span
        onClick={() => onChange(!checked)}
        className={`w-10 h-5 rounded-full transition-colors relative ${checked ? "bg-[#6FA3A6]" : "bg-[#E5E0D8]"}`}
      >
        <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${checked ? "left-5" : "left-0.5"}`} />
      </span>
      <span className="text-sm text-[#5C544E]">{label}</span>
    </label>
  );
}

function HistoryCard({ item, reload }) {
  const p = item.professor || {};
  const [received, setReceived] = useState(!!item.response_received);
  const [interested, setInterested] = useState(!!item.is_interested);
  const [notes, setNotes] = useState(item.response_notes || "");

  const save = async () => {
    await api.updateOutreach(item.id, {
      response_received: received,
      is_interested: interested,
      response_notes: notes,
    });
    toast.success("Saved");
    reload();
  };

  return (
    <div className="bg-white border border-[#E5E0D8] rounded-xl p-5" data-testid={`history-card-${item.id}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="font-medium text-[#2A2522]">{p.name}</span>
            <TrackChip track={p.best_track} />
            {item.manual && <span className="text-[10px] uppercase tracking-wider text-[#8A8179] border border-[#E5E0D8] rounded px-1.5 py-0.5">manual</span>}
          </div>
          <div className="text-xs text-[#8A8179] mt-0.5">{p.university} {p.email ? `· ${p.email}` : ""}</div>
        </div>
        <div className="text-right text-xs text-[#8A8179]">
          <div className="uppercase tracking-wider text-[#6FA3A6] font-semibold">{item.status}</div>
          {item.sent_at && <div>{new Date(item.sent_at).toLocaleDateString()}</div>}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-6 mt-4">
        <Toggle checked={received} onChange={setReceived} label="Response received" testid={`toggle-received-${item.id}`} />
        <Toggle checked={interested} onChange={setInterested} label="Interested" testid={`toggle-interested-${item.id}`} />
      </div>

      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Response notes..."
        data-testid={`notes-${item.id}`}
        className="w-full mt-3 h-20 bg-[#FDFCFB] border border-[#E5E0D8] rounded-md p-3 text-sm text-[#2A2522] focus:outline-none focus:ring-2 focus:ring-[#6FA3A6]/50 resize-y"
      />
      <button
        onClick={save}
        data-testid={`save-history-${item.id}`}
        className="mt-3 bg-[#A64B2A] text-white hover:bg-[#8A3E22] transition-colors px-5 py-1.5 rounded-md font-medium text-sm"
      >
        Save
      </button>
    </div>
  );
}

function ManualForm({ reload }) {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ name: "", university: "", email: "", focus: "", response_received: false, is_interested: false, response_notes: "" });

  const submit = async () => {
    if (!f.name.trim()) return toast.error("Name is required");
    await api.addManual({ ...f, status: "sent" });
    toast.success("Manual entry added");
    setF({ name: "", university: "", email: "", focus: "", response_received: false, is_interested: false, response_notes: "" });
    setOpen(false);
    reload();
  };

  const inp = "w-full bg-[#FDFCFB] border border-[#E5E0D8] rounded-md px-4 py-2 text-[#2A2522] focus:outline-none focus:ring-2 focus:ring-[#6FA3A6]/50";

  return (
    <div className="bg-white border border-[#E5E0D8] rounded-xl mb-6">
      <button
        onClick={() => setOpen(!open)}
        data-testid="manual-expander"
        className="w-full flex items-center gap-2 p-4 text-left font-medium text-[#A64B2A] hover:bg-[#F8F5F0] transition-colors rounded-xl"
      >
        <Plus size={18} weight="bold" /> Add manually (professor contacted outside the app)
      </button>
      {open && (
        <div className="p-5 border-t border-[#E5E0D8] space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <input data-testid="manual-name" className={inp} placeholder="Name *" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
            <input data-testid="manual-university" className={inp} placeholder="University" value={f.university} onChange={(e) => setF({ ...f, university: e.target.value })} />
            <input data-testid="manual-email" className={inp} placeholder="Email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} />
            <input data-testid="manual-focus" className={inp} placeholder="Research focus" value={f.focus} onChange={(e) => setF({ ...f, focus: e.target.value })} />
          </div>
          <div className="flex gap-6">
            <Toggle checked={f.response_received} onChange={(v) => setF({ ...f, response_received: v })} label="Response received" testid="manual-received" />
            <Toggle checked={f.is_interested} onChange={(v) => setF({ ...f, is_interested: v })} label="Interested" testid="manual-interested" />
          </div>
          <textarea className={inp + " h-16 resize-y"} placeholder="Notes" value={f.response_notes} onChange={(e) => setF({ ...f, response_notes: e.target.value })} data-testid="manual-notes" />
          <button onClick={submit} data-testid="manual-submit" className="bg-[#A64B2A] text-white hover:bg-[#8A3E22] transition-colors px-6 py-2 rounded-md font-medium text-sm">
            Add entry
          </button>
        </div>
      )}
    </div>
  );
}

export default function History({ history, reload }) {
  return (
    <div className="fade-up">
      <ManualForm reload={reload} />
      {history.length === 0 ? (
        <div className="text-center py-20">
          <ClockCounterClockwise size={56} className="mx-auto text-[#6FA3A6] mb-4" />
          <h3 className="font-serif-display text-2xl text-[#A64B2A]">No outreach history</h3>
          <p className="text-[#8A8179] mt-1">Sent and skipped professors will appear here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((h, i) => (
            <motion.div key={h.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i * 0.04, 0.4) }}>
              <HistoryCard item={h} reload={reload} />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
