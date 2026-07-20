"""End-to-end backend API tests for PhD Outreach Agent.
Runs sequentially (LLM key rejects concurrent requests)."""
import os
import time
import pytest
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
FRONTEND_ENV = Path(__file__).resolve().parents[2] / "frontend" / ".env"
if FRONTEND_ENV.exists():
    load_dotenv(FRONTEND_ENV)

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"
TIMEOUT = 180  # LLM calls can take time

state = {}


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- Profile & Tracks ----------
def test_tracks(s):
    r = s.get(f"{API}/tracks", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) == 8
    keys = [t["key"] for t in data]
    assert "attention" in keys
    for t in data:
        assert "label" in t and "doc_focus" in t


def test_profile_get(s):
    r = s.get(f"{API}/profile", timeout=30)
    assert r.status_code == 200
    p = r.json()
    assert p["name"] == "Radhika Prakash Chhabria"
    for k in ("base_cv", "base_proposal", "sample_email", "summary"):
        assert p.get(k)


def test_profile_put(s):
    original = s.get(f"{API}/profile").json()
    new_summary = original["summary"] + " [TEST_APPEND]"
    r = s.put(f"{API}/profile", json={"summary": new_summary}, timeout=30)
    assert r.status_code == 200
    assert r.json()["summary"] == new_summary
    # verify persistence
    got = s.get(f"{API}/profile").json()
    assert got["summary"] == new_summary
    # revert
    s.put(f"{API}/profile", json={"summary": original["summary"]}, timeout=30)


# ---------- Discovery ----------
def test_discover(s):
    r = s.post(f"{API}/discover",
               json={"per_track": 1, "only_track": "attention"}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "professors" in data
    if data["created"] == 0 and data.get("errors"):
        pytest.skip(f"LLM discovery errors: {data['errors']}")
    # Use returned professor if any created; otherwise use highest-ranked existing
    if data["created"] >= 1:
        p = data["professors"][0]
    else:
        # duplicates skipped - fall back to existing prof without outreach
        profs = s.get(f"{API}/professors").json()
        candidates = [x for x in profs if not x.get("outreach_status") and x.get("match_score", 0) > 0]
        assert candidates, "no eligible professors"
        p = candidates[0]
    for f in ("score_research", "score_methods", "score_lab_activity",
              "score_program", "match_score", "best_track", "taking_students"):
        assert f in p, f"missing {f}"
    assert 0 <= p["match_score"] <= 1
    state["prof_id"] = p["id"]


def test_list_professors_sorted(s):
    r = s.get(f"{API}/professors", timeout=30)
    assert r.status_code == 200
    profs = r.json()
    assert len(profs) >= 1
    scores = [p["match_score"] for p in profs]
    assert scores == sorted(scores, reverse=True)
    assert "outreach_status" in profs[0]


# ---------- Brief & Docs (SEQUENTIAL) ----------
def test_brief(s):
    pid = state.get("prof_id")
    if not pid:
        pytest.skip("no professor from discovery")
    r = s.post(f"{API}/professors/{pid}/brief", timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    assert r.json()["brief_md"]
    # verify persisted
    p = s.get(f"{API}/professors/{pid}").json()
    assert p["brief_md"]


@pytest.mark.parametrize("doc_type", ["cv", "sop", "proposal"])
def test_generate_docs(s, doc_type):
    pid = state.get("prof_id")
    if not pid:
        pytest.skip("no professor")
    time.sleep(2)  # avoid concurrency issues
    r = s.post(f"{API}/professors/{pid}/generate/{doc_type}", timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["doc_type"] == doc_type
    assert j["content"]


def test_generate_email(s):
    pid = state.get("prof_id")
    if not pid:
        pytest.skip("no professor")
    time.sleep(2)
    r = s.post(f"{API}/professors/{pid}/generate/email", timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["doc_type"] == "email"
    assert j["body"]
    # outreach draft created
    pending = s.get(f"{API}/outreach/pending").json()
    assert any(p["id"] == pid for p in pending)


# ---------- Outreach flow ----------
def test_mark_sent_moves_to_history(s):
    pid = state.get("prof_id")
    if not pid:
        pytest.skip("no professor")
    r = s.post(f"{API}/outreach/{pid}/send", timeout=30)
    assert r.status_code == 200
    pending = s.get(f"{API}/outreach/pending").json()
    assert not any(p["id"] == pid for p in pending)
    history = s.get(f"{API}/outreach/history").json()
    match = [o for o in history if o["professor_id"] == pid]
    assert match and match[0]["status"] == "sent"
    state["outreach_id"] = match[0]["id"]


def test_patch_outreach_replied(s):
    oid = state.get("outreach_id")
    if not oid:
        pytest.skip("no outreach id")
    r = s.patch(f"{API}/outreach/{oid}",
                json={"response_received": True, "is_interested": True,
                      "response_notes": "TEST_REPLIED"}, timeout=30)
    assert r.status_code == 200, r.text
    o = r.json()
    assert o["status"] == "replied"
    assert o["response_received"] == 1
    assert o["is_interested"] == 1
    assert o["response_notes"] == "TEST_REPLIED"


def test_skip_creates_closed(s):
    # create manual entry then skip via different professor
    # instead do skip on a new manual prof to avoid interfering
    r = s.post(f"{API}/outreach/manual",
               json={"name": "TEST_SkipProf", "university": "T U", "status": "drafted"}, timeout=30)
    assert r.status_code == 200
    pid = r.json()["professor_id"]
    r2 = s.post(f"{API}/outreach/{pid}/skip", timeout=30)
    assert r2.status_code == 200
    history = s.get(f"{API}/outreach/history").json()
    assert any(o["professor_id"] == pid and o["status"] == "closed" for o in history)


def test_manual_outreach_in_history(s):
    r = s.post(f"{API}/outreach/manual",
               json={"name": "TEST_ManualProf", "university": "Test U",
                     "email": "test@test.edu", "focus": "attention",
                     "status": "sent", "response_received": False,
                     "is_interested": False, "response_notes": ""}, timeout=30)
    assert r.status_code == 200
    pid = r.json()["professor_id"]
    history = s.get(f"{API}/outreach/history").json()
    assert any(o["professor_id"] == pid for o in history)


def test_stats(s):
    r = s.get(f"{API}/stats", timeout=30)
    assert r.status_code == 200
    d = r.json()
    for k in ("professors", "sent", "replied", "interested"):
        assert k in d and isinstance(d[k], int)
    assert d["professors"] >= 1
    assert d["sent"] >= 1
