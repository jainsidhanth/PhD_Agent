"""Claude (Anthropic) calls: discovery, brief, documents.

Uses the official Anthropic SDK with your own ANTHROPIC_API_KEY, so the app has
no dependency on any hosting provider and can be self-hosted anywhere.
"""
import os
import json
import re
from anthropic import AsyncAnthropic

from domain import TRACK_MAP, PROFILE_SUMMARY

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _sanitize(text):
    if not text:
        return text
    return text.replace("\u2014", "-").replace("\u2013", "-")


async def _complete(system, prompt, max_tokens=4096):
    resp = await client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return _sanitize("".join(parts))


def _extract_json(text):
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


REGION_LABELS = {"us": "the United States", "europe": "Europe"}


async def discover_professors(track_key, count, profile_summary=None, region=None):
    track = TRACK_MAP[track_key]
    profile_summary = profile_summary or PROFILE_SUMMARY
    system = (
        "You are a research assistant helping a PhD applicant build a shortlist of potential "
        "PhD supervisors. Return realistic, well-known academic profiles that plausibly match "
        "the requested research area. Base entries on your knowledge of real active labs and "
        "researchers in cognitive neuroscience and psychology. "
        "Never use em-dashes or en-dashes; use a hyphen. Output ONLY a valid JSON array, no prose."
    )
    region_line = ""
    if region in REGION_LABELS:
        region_line = f'\nRestrict results to universities located in {REGION_LABELS[region]}. Do not include professors from any other region.'
    prompt = f"""Find {count} professors who supervise PhD students in the research area: "{track['label']}".
{region_line}
Applicant background (for relevance): {profile_summary}

For each professor return an object with EXACTLY these fields:
- "name": full name with title (e.g. "Prof. Jane Smith")
- "university": institution name
- "program_name": department or program name
- "email": a plausible institutional email if commonly known, else null
- "focus": 1-2 sentence description of their research focus, using terminology from "{track['label']}"
- "recent_papers": array of 1-2 realistic recent paper titles
- "taking_students": one of "yes", "no", or "unknown" (use "unknown" unless clearly known)
- "rank": approximate global university rank as an integer, or null if unsure

Return a JSON array of {count} objects. No text outside the array."""

    text = await _complete(system, prompt, max_tokens=2048)
    data = _extract_json(text)
    cleaned = []
    for d in data:
        if not isinstance(d, dict) or not d.get("name"):
            continue
        cleaned.append({
            "name": _sanitize(str(d.get("name", "")).strip()),
            "university": _sanitize(str(d.get("university", "") or "").strip()),
            "program_name": _sanitize(str(d.get("program_name", "") or "").strip()),
            "email": (str(d.get("email")).strip() if d.get("email") else None),
            "focus": _sanitize(str(d.get("focus", "") or "").strip()),
            "recent_papers": [_sanitize(str(p).strip()) for p in (d.get("recent_papers") or [])][:2],
            "taking_students": d.get("taking_students") if d.get("taking_students") in ("yes", "no", "unknown") else "unknown",
            "rank": d.get("rank") if isinstance(d.get("rank"), int) else None,
        })
    return cleaned


async def generate_brief(prof, profile):
    system = (
        "You are a research assistant writing a concise, structured one-page brief for a PhD "
        "applicant about a potential supervisor. Be specific and honest. "
        "Never use em-dashes or en-dashes; use a hyphen. Use clean Markdown."
    )
    track = TRACK_MAP.get(prof.get("best_track"), {})
    prompt = f"""Applicant: {profile.get('summary')}

Suggested angle: {track.get('doc_focus', '')}

Professor: {prof.get('name')} - {prof.get('university')}
Focus: {prof.get('focus')}
Recent papers: {', '.join(prof.get('recent_papers') or []) or 'n/a'}
Taking students: {prof.get('taking_students')}

Write a one-page brief in Markdown with these sections:
## Lab Overview
## Key Papers in Plain English
## Why This Lab Fits Radhika
## Best Hook Angle for the Email
## Watch-Out Flags"""
    return await _complete(system, prompt, max_tokens=2048)


DOC_SPECS = {
    "cv": ("a tailored CV in Markdown (~1 page)",
           "Reframe the applicant's CV to foreground experience most relevant to this professor. "
           "Use ONLY facts from the base CV; never invent credentials."),
    "sop": ("a Statement of Purpose (~900 words) in Markdown",
            "Write a compelling SOP tailored to this professor's lab, grounded in the base CV and proposal."),
    "proposal": ("a research proposal (~1 page) in Markdown",
                 "Adapt the base proposal to this professor's research area while keeping the DDM/RL core."),
    "email": ("a plain-text cold outreach email",
              "Write a concise, personalised outreach email using the sample email as a tone/structure reference. "
              "Reference the professor's specific work. Return the email body only, starting with 'Subject:'."),
}


async def generate_document(doc_type, prof, profile):
    label, instruction = DOC_SPECS[doc_type]
    track = TRACK_MAP.get(prof.get("best_track"), {})
    system = (
        "You are an expert academic writing assistant helping a PhD applicant. "
        "Use only truthful information from the provided ground-truth materials; never fabricate "
        "credentials, publications, or experience. "
        "Never use em-dashes or en-dashes; always use a plain hyphen."
    )
    prompt = f"""Produce {label}.
{instruction}

Suggested emphasis for this professor: {track.get('doc_focus', '')}

--- APPLICANT PROFILE ---
{profile.get('summary')}

--- BASE CV ---
{profile.get('base_cv')}

--- BASE PROPOSAL ---
{profile.get('base_proposal')}

--- SAMPLE EMAIL (tone/structure reference) ---
{profile.get('sample_email')}

--- TARGET PROFESSOR ---
Name: {prof.get('name')}
University: {prof.get('university')}
Focus: {prof.get('focus')}
Recent papers: {', '.join(prof.get('recent_papers') or []) or 'n/a'}
"""
    return await _complete(system, prompt, max_tokens=4096)
