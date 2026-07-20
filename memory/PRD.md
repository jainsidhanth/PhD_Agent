# PhD Outreach Agent — PRD

## Original Problem Statement
An AI-powered single-user tool that discovers, evaluates, and manages cold outreach to PhD
supervisors worldwide — replacing a spreadsheet and hours of manual CV tailoring. Ported from the
PRD's Streamlit/SQLite spec to this platform's **React + FastAPI + MongoDB** stack.

## User Persona
Radhika Prakash Chhabria — PhD applicant, MSc Cognitive Neuroscience (Durham) + MSc Clinical
Psychology. Methods: EyeLink eye-tracking, EEG, fMRI, MATLAB/R/SPSS/Python; ABCD/UK Biobank/PPMI.

## Architecture / Stack
- Frontend: React (sidebar nav, 4 tabs), Phosphor icons, Framer Motion, Tailwind. Palette: burnt
  orange #A64B2A, gold #E6A64B, teal #6FA3A6, off-white #F8F5F0. Fonts: Cormorant Garamond + Manrope.
- Backend: FastAPI, all routes under /api.
- DB: MongoDB collections — profile, professors, outreach, documents.
- LLM: Claude Sonnet 4.6 via Emergent LLM key (emergentintegrations). Discovery uses model
  knowledge (no live web search per user choice). NOTE: key has no parallel-request support.
- Scoring: offline keyword-saturation scorer (domain.py) — research/methods/lab-activity/program.

## User Choices
- LLM: Claude Sonnet 4.6 · Discovery: LLM built-in knowledge · Scope: core 3 tabs + Profile editor.

## Implemented (2026-06)
- Discover: Find Professors (per-track count + track filter), ranked table with 5 progress-bar
  score columns, taking-students badges, track chips.
- 4-dimensional scoring per PRD formula (content*0.6 + methods*0.4 + content*methods*0.1).
- Outreach: collapsible cards, Generate Brief -> Generate Package (sequential CV/SOP/proposal/email),
  email copy area, Mark as Sent / Skip. Em-dash sanitisation on all LLM output.
- History: response/interested toggles + notes, reverse-chronological, Add-manually form.
- Profile editor: base CV / proposal / sample email / summary (ground truth, editable).
- Sidebar stats (professors/sent/replies/interested).
- Tested end-to-end: backend 15/15 pytest pass, frontend Playwright 100%.

## Deferred / Backlog
- P1: .docx export of CV/SOP/proposal (currently Markdown content stored, no file download yet).
- P1: Gmail OAuth draft creation with attachments (non-goal v1, PRD roadmap).
- P2: Re-run discovery to refresh taking_students; program-rank enrichment (QS/THE).
- P2: LinkedIn draft, deadline tracker, batch package generation, side-by-side comparison,
  auto follow-up scheduler, cloud hosting.

## Known Limitations
- Discovery uses LLM knowledge, not verified live web search (per user choice) — profiles are
  realistic but should be verified before contact.
- taking_students often "unknown"; program score defaults to 0.50 when rank unknown.
- LLM key rejects concurrent requests; generation steps run sequentially.
