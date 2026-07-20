import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import { Toaster } from "@/components/ui/sonner";
import {
  MagnifyingGlass, PaperPlaneTilt, ClockCounterClockwise, UserCircle, GraduationCap,
} from "@phosphor-icons/react";
import { api } from "./api";
import Discover from "./pages/Discover";
import Outreach from "./pages/Outreach";
import History from "./pages/History";
import Profile from "./pages/Profile";

const NAV = [
  { key: "discover", label: "Discover", icon: MagnifyingGlass },
  { key: "outreach", label: "Outreach", icon: PaperPlaneTilt },
  { key: "history", label: "History", icon: ClockCounterClockwise },
  { key: "profile", label: "Profile", icon: UserCircle },
];

function App() {
  const [tab, setTab] = useState("discover");
  const [professors, setProfessors] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [pending, setPending] = useState([]);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState({ professors: 0, sent: 0, replied: 0, interested: 0 });

  const reload = useCallback(async () => {
    const [profs, pend, hist, st] = await Promise.all([
      api.getProfessors(), api.pending(), api.history(), api.stats(),
    ]);
    setProfessors(profs);
    setPending(pend);
    setHistory(hist);
    setStats(st);
  }, []);

  useEffect(() => {
    api.getTracks().then(setTracks);
    reload();
  }, [reload]);

  return (
    <div className="App flex min-h-screen bg-[#F8F5F0]">
      <Toaster position="top-right" richColors />

      {/* Sidebar */}
      <aside className="w-64 shrink-0 bg-white border-r border-[#E5E0D8] flex flex-col fixed h-screen">
        <div className="p-6 border-b border-[#E5E0D8]">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-[#A64B2A] flex items-center justify-center">
              <GraduationCap size={22} weight="fill" className="text-white" />
            </div>
            <div>
              <h1 className="font-serif-display text-xl font-semibold text-[#A64B2A] leading-none">PhD Outreach</h1>
              <span className="text-[10px] uppercase tracking-[0.18em] text-[#8A8179]">Agent v1.1</span>
            </div>
          </div>
        </div>

        <nav className="p-3 flex-1">
          {NAV.map((n) => {
            const Icon = n.icon;
            const active = tab === n.key;
            const badge = n.key === "outreach" ? pending.length : n.key === "history" ? history.length : 0;
            return (
              <button
                key={n.key}
                data-testid={`nav-${n.key}`}
                onClick={() => setTab(n.key)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg mb-1 text-sm font-medium transition-colors ${
                  active ? "bg-[#F0EBE1] text-[#A64B2A]" : "text-[#5C544E] hover:bg-[#F8F5F0]"
                }`}
              >
                <Icon size={19} weight={active ? "fill" : "regular"} />
                <span className="flex-1 text-left">{n.label}</span>
                {badge > 0 && (
                  <span className="text-xs font-mono px-1.5 py-0.5 rounded-full bg-[#6FA3A6]/15 text-[#4d7a7c]">{badge}</span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-[#E5E0D8] grid grid-cols-2 gap-2">
          {[
            ["Professors", stats.professors],
            ["Sent", stats.sent],
            ["Replies", stats.replied],
            ["Interested", stats.interested],
          ].map(([label, val]) => (
            <div key={label} className="bg-[#FDFCFB] border border-[#E5E0D8] rounded-lg p-2.5 text-center">
              <div className="text-lg font-mono font-semibold text-[#A64B2A]">{val}</div>
              <div className="text-[10px] uppercase tracking-wider text-[#8A8179]">{label}</div>
            </div>
          ))}
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 ml-64 p-10 max-w-[1400px]">
        <header className="mb-8">
          <p className="text-xs font-semibold tracking-[0.15em] uppercase text-[#6FA3A6] mb-1">
            {tab === "discover" && "Find & score supervisors"}
            {tab === "outreach" && "Prepare tailored packages"}
            {tab === "history" && "Track responses"}
            {tab === "profile" && "Ground-truth materials"}
          </p>
          <h2 className="font-serif-display text-4xl font-semibold text-[#A64B2A] capitalize">{tab}</h2>
        </header>

        {tab === "discover" && <Discover professors={professors} tracks={tracks} reload={reload} />}
        {tab === "outreach" && <Outreach pending={pending} reload={reload} />}
        {tab === "history" && <History history={history} reload={reload} />}
        {tab === "profile" && <Profile />}
      </main>
    </div>
  );
}

export default App;
