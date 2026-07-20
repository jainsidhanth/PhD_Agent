import React, { useState, useEffect } from "react";
import { FloppyDisk } from "@phosphor-icons/react";
import { toast } from "sonner";
import { api } from "../api";

function Field({ label, hint, value, onChange, rows = 10, testid }) {
  return (
    <div>
      <label className="block text-sm font-semibold text-[#2A2522]">{label}</label>
      {hint && <p className="text-xs text-[#8A8179] mb-2">{hint}</p>}
      <textarea
        data-testid={testid}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="w-full bg-[#FDFCFB] border border-[#E5E0D8] rounded-md p-4 text-sm text-[#2A2522] font-mono focus:outline-none focus:ring-2 focus:ring-[#6FA3A6]/50 resize-y"
      />
    </div>
  );
}

export default function Profile() {
  const [p, setP] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.getProfile().then(setP); }, []);

  const save = async () => {
    setSaving(true);
    try {
      await api.updateProfile({
        name: p.name, summary: p.summary, base_cv: p.base_cv,
        base_proposal: p.base_proposal, sample_email: p.sample_email,
      });
      toast.success("Profile saved. These are used as ground truth for all generation.");
    } catch { toast.error("Save failed"); }
    finally { setSaving(false); }
  };

  if (!p) return <div className="text-[#8A8179]">Loading...</div>;

  const set = (k) => (v) => setP({ ...p, [k]: v });

  return (
    <div className="fade-up max-w-3xl space-y-6">
      <div className="bg-white border border-[#E5E0D8] rounded-xl p-6 space-y-6">
        <div>
          <label className="block text-sm font-semibold text-[#2A2522] mb-2">Candidate name</label>
          <input
            data-testid="profile-name"
            value={p.name || ""}
            onChange={(e) => set("name")(e.target.value)}
            className="w-full bg-[#FDFCFB] border border-[#E5E0D8] rounded-md px-4 py-2 text-[#2A2522] focus:outline-none focus:ring-2 focus:ring-[#6FA3A6]/50"
          />
        </div>
        <Field label="Profile summary" hint="Used by the LLM for scoring and generation." value={p.summary} onChange={set("summary")} rows={4} testid="profile-summary" />
        <Field label="Base CV (Markdown)" hint="Ground-truth CV. The generator reframes but never invents facts." value={p.base_cv} onChange={set("base_cv")} testid="profile-cv" />
        <Field label="Base research proposal (Markdown)" hint="Core DDM/RL proposal, adapted per professor." value={p.base_proposal} onChange={set("base_proposal")} testid="profile-proposal" />
        <Field label="Sample outreach email" hint="Tone and structure reference for generated emails." value={p.sample_email} onChange={set("sample_email")} testid="profile-email" />
        <button
          onClick={save} disabled={saving}
          data-testid="profile-save-btn"
          className="inline-flex items-center gap-2 bg-[#A64B2A] text-white hover:bg-[#8A3E22] transition-colors px-6 py-2.5 rounded-md font-medium disabled:opacity-60"
        >
          <FloppyDisk size={18} /> {saving ? "Saving..." : "Save profile"}
        </button>
      </div>
    </div>
  );
}
