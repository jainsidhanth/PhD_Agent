from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import io
import re
import logging
import uuid
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from domain import TRACKS, TRACK_MAP, DEFAULT_PROFILE, score_professor, _rank_score
import llm_service
from docgen import markdown_to_docx

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------- Models ----------
class DiscoverRequest(BaseModel):
    per_track: int = 2
    only_track: Optional[str] = None


class RankUpdate(BaseModel):
    rank: Optional[int] = None



class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    summary: Optional[str] = None
    base_cv: Optional[str] = None
    base_proposal: Optional[str] = None
    sample_email: Optional[str] = None


class OutreachUpdate(BaseModel):
    response_received: Optional[bool] = None
    is_interested: Optional[bool] = None
    response_notes: Optional[str] = None
    replied_at: Optional[str] = None


class ManualEntry(BaseModel):
    name: str
    university: Optional[str] = ""
    email: Optional[str] = None
    focus: Optional[str] = ""
    status: str = "sent"
    response_received: bool = False
    is_interested: bool = False
    response_notes: Optional[str] = ""


# ---------- Helpers ----------
async def get_profile_doc():
    doc = await db.profile.find_one({"id": "default"}, {"_id": 0})
    if not doc:
        await db.profile.insert_one(dict(DEFAULT_PROFILE))
        doc = dict(DEFAULT_PROFILE)
    return doc


# ---------- Profile ----------
@api_router.get("/profile")
async def read_profile():
    return await get_profile_doc()


@api_router.put("/profile")
async def update_profile(payload: ProfileUpdate):
    await get_profile_doc()
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if updates:
        await db.profile.update_one({"id": "default"}, {"$set": updates})
    return await get_profile_doc()


# ---------- Tracks ----------
@api_router.get("/tracks")
async def read_tracks():
    return [{"key": t["key"], "label": t["label"], "doc_focus": t["doc_focus"]} for t in TRACKS]


# ---------- Discovery ----------
@api_router.post("/discover")
async def discover(req: DiscoverRequest):
    profile = await get_profile_doc()
    per_track = max(1, min(5, req.per_track))
    track_keys = [req.only_track] if req.only_track and req.only_track in TRACK_MAP else [t["key"] for t in TRACKS]

    created = []
    errors = []
    for tk in track_keys:
        try:
            found = await llm_service.discover_professors(tk, per_track, profile.get("summary"))
        except Exception as e:
            logger.exception("discover failed for %s", tk)
            errors.append(f"{tk}: {e}")
            continue
        for f in found:
            existing = await db.professors.find_one(
                {"name": f["name"], "university": f["university"]}, {"_id": 0})
            if existing:
                continue
            scores = score_professor(f)
            prof = {
                "id": str(uuid.uuid4()),
                "name": f["name"],
                "university": f["university"],
                "program_name": f.get("program_name", ""),
                "email": f.get("email"),
                "focus": f.get("focus", ""),
                "recent_papers": f.get("recent_papers", []),
                "taking_students": f.get("taking_students", "unknown"),
                "rank": f.get("rank"),
                "brief_md": None,
                "created_at": now_iso(),
                **scores,
            }
            await db.professors.insert_one(dict(prof))
            prof.pop("_id", None)
            created.append(prof)

    return {"created": len(created), "professors": created, "errors": errors}


# ---------- Professors ----------
@api_router.get("/professors")
async def list_professors():
    profs = await db.professors.find({}, {"_id": 0}).to_list(1000)
    # attach outreach status
    outreaches = {o["professor_id"]: o for o in await db.outreach.find({}, {"_id": 0}).to_list(1000)}
    for p in profs:
        o = outreaches.get(p["id"])
        p["outreach_status"] = o["status"] if o else None
    profs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return profs


@api_router.get("/professors/{prof_id}")
async def get_professor(prof_id: str):
    p = await db.professors.find_one({"id": prof_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Professor not found")
    return p


@api_router.patch("/professors/{prof_id}/rank")
async def update_rank(prof_id: str, payload: RankUpdate):
    p = await db.professors.find_one({"id": prof_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Professor not found")
    rank = payload.rank
    score_program = _rank_score(rank)
    await db.professors.update_one(
        {"id": prof_id}, {"$set": {"rank": rank, "score_program": score_program}})
    p["rank"] = rank
    p["score_program"] = score_program
    return p


def _slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name or "professor").strip("_")


@api_router.get("/professors/{prof_id}/download/{doc_type}")
async def download_doc(prof_id: str, doc_type: str):
    if doc_type not in ("cv", "sop", "proposal"):
        raise HTTPException(400, "Invalid doc_type")
    prof = await db.professors.find_one({"id": prof_id}, {"_id": 0})
    doc = await db.documents.find_one({"professor_id": prof_id, "doc_type": doc_type}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Document not generated yet")
    title_map = {"cv": "Curriculum Vitae", "sop": "Statement of Purpose", "proposal": "Research Proposal"}
    data = markdown_to_docx(doc["content_md"], title=title_map[doc_type])
    prof_slug = _slug(prof.get("name") if prof else "professor")
    filename = f"{prof_slug}_{doc_type}.docx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api_router.post("/professors/{prof_id}/brief")
async def make_brief(prof_id: str):
    prof = await db.professors.find_one({"id": prof_id}, {"_id": 0})
    if not prof:
        raise HTTPException(404, "Professor not found")
    profile = await get_profile_doc()
    brief = await llm_service.generate_brief(prof, profile)
    await db.professors.update_one({"id": prof_id}, {"$set": {"brief_md": brief}})
    return {"brief_md": brief}


@api_router.post("/professors/{prof_id}/generate/{doc_type}")
async def generate_one(prof_id: str, doc_type: str):
    if doc_type not in ("cv", "sop", "proposal", "email"):
        raise HTTPException(400, "Invalid doc_type")
    prof = await db.professors.find_one({"id": prof_id}, {"_id": 0})
    if not prof:
        raise HTTPException(404, "Professor not found")
    profile = await get_profile_doc()

    content = await llm_service.generate_document(doc_type, prof, profile)

    if doc_type != "email":
        await db.documents.delete_many({"professor_id": prof_id, "doc_type": doc_type})
        await db.documents.insert_one({
            "id": str(uuid.uuid4()),
            "professor_id": prof_id,
            "doc_type": doc_type,
            "content_md": content,
            "generated_at": now_iso(),
        })
        return {"doc_type": doc_type, "content": content}

    # email: parse subject/body and store outreach draft
    subject, body = "", content
    for line in content.splitlines():
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body = content.replace(line, "", 1).strip()
            break

    existing = await db.outreach.find_one({"professor_id": prof_id}, {"_id": 0})
    if existing:
        new_status = existing["status"] if existing["status"] != "closed" else "drafted"
        await db.outreach.update_one({"professor_id": prof_id},
            {"$set": {"draft_subject": subject, "draft_body": body, "status": new_status}})
    else:
        await db.outreach.insert_one({
            "id": str(uuid.uuid4()), "professor_id": prof_id, "status": "drafted",
            "draft_subject": subject, "draft_body": body, "sent_at": None, "replied_at": None,
            "response_received": 0, "is_interested": 0, "response_notes": "",
            "manual": False, "created_at": now_iso(),
        })
    return {"doc_type": "email", "content": content, "subject": subject, "body": body}


@api_router.get("/professors/{prof_id}/documents")
async def get_documents(prof_id: str):
    docs = await db.documents.find({"professor_id": prof_id}, {"_id": 0}).to_list(100)
    return docs


# ---------- Outreach ----------
async def enrich_outreach(o):
    prof = await db.professors.find_one({"id": o["professor_id"]}, {"_id": 0})
    o["professor"] = prof
    return o


@api_router.get("/outreach/pending")
async def outreach_pending():
    """Scored professors not yet sent/closed."""
    profs = await db.professors.find({}, {"_id": 0}).to_list(1000)
    outreaches = {o["professor_id"]: o for o in await db.outreach.find({}, {"_id": 0}).to_list(1000)}
    result = []
    for p in profs:
        o = outreaches.get(p["id"])
        if o and o["status"] in ("sent", "replied", "closed"):
            continue
        p["outreach"] = o
        result.append(p)
    result.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return result


@api_router.get("/outreach/history")
async def outreach_history():
    outreaches = await db.outreach.find(
        {"status": {"$in": ["sent", "replied", "closed"]}}, {"_id": 0}).to_list(1000)
    for o in outreaches:
        await enrich_outreach(o)
    outreaches.sort(key=lambda x: x.get("sent_at") or x.get("created_at") or "", reverse=True)
    return outreaches


@api_router.post("/outreach/{prof_id}/send")
async def mark_sent(prof_id: str):
    o = await db.outreach.find_one({"professor_id": prof_id}, {"_id": 0})
    ts = now_iso()
    if not o:
        await db.outreach.insert_one({
            "id": str(uuid.uuid4()), "professor_id": prof_id, "status": "sent",
            "draft_subject": "", "draft_body": "", "sent_at": ts, "replied_at": None,
            "response_received": 0, "is_interested": 0, "response_notes": "",
            "manual": False, "created_at": ts,
        })
    else:
        await db.outreach.update_one({"professor_id": prof_id},
            {"$set": {"status": "sent", "sent_at": ts}})
    return {"ok": True}


@api_router.post("/outreach/{prof_id}/skip")
async def skip(prof_id: str):
    o = await db.outreach.find_one({"professor_id": prof_id}, {"_id": 0})
    ts = now_iso()
    if not o:
        await db.outreach.insert_one({
            "id": str(uuid.uuid4()), "professor_id": prof_id, "status": "closed",
            "draft_subject": "", "draft_body": "", "sent_at": None, "replied_at": None,
            "response_received": 0, "is_interested": 0, "response_notes": "",
            "manual": False, "created_at": ts,
        })
    else:
        await db.outreach.update_one({"professor_id": prof_id}, {"$set": {"status": "closed"}})
    return {"ok": True}


@api_router.patch("/outreach/{outreach_id}")
async def update_outreach(outreach_id: str, payload: OutreachUpdate):
    updates = {}
    d = payload.model_dump()
    if d.get("response_received") is not None:
        updates["response_received"] = 1 if d["response_received"] else 0
        updates["status"] = "replied" if d["response_received"] else "sent"
        if d["response_received"] and not d.get("replied_at"):
            updates["replied_at"] = now_iso()
    if d.get("is_interested") is not None:
        updates["is_interested"] = 1 if d["is_interested"] else 0
    if d.get("response_notes") is not None:
        updates["response_notes"] = d["response_notes"]
    if updates:
        await db.outreach.update_one({"id": outreach_id}, {"$set": updates})
    o = await db.outreach.find_one({"id": outreach_id}, {"_id": 0})
    if not o:
        raise HTTPException(404, "Outreach not found")
    return await enrich_outreach(o)


@api_router.post("/outreach/manual")
async def add_manual(entry: ManualEntry):
    ts = now_iso()
    prof = {
        "id": str(uuid.uuid4()), "name": entry.name, "university": entry.university or "",
        "program_name": "", "email": entry.email, "focus": entry.focus or "",
        "recent_papers": [], "taking_students": "unknown", "rank": None, "brief_md": None,
        "created_at": ts,
        "best_track": None, "score_research": 0, "score_methods": 0,
        "score_lab_activity": 0, "score_program": 0, "match_score": 0,
    }
    await db.professors.insert_one(dict(prof))
    await db.outreach.insert_one({
        "id": str(uuid.uuid4()), "professor_id": prof["id"], "status": entry.status,
        "draft_subject": "", "draft_body": "", "sent_at": ts if entry.status != "drafted" else None,
        "replied_at": ts if entry.response_received else None,
        "response_received": 1 if entry.response_received else 0,
        "is_interested": 1 if entry.is_interested else 0,
        "response_notes": entry.response_notes or "", "manual": True, "created_at": ts,
    })
    return {"ok": True, "professor_id": prof["id"]}


@api_router.get("/stats")
async def stats():
    total_profs = await db.professors.count_documents({})
    sent = await db.outreach.count_documents({"status": {"$in": ["sent", "replied"]}})
    replied = await db.outreach.count_documents({"response_received": 1})
    interested = await db.outreach.count_documents({"is_interested": 1})
    return {"professors": total_profs, "sent": sent, "replied": replied, "interested": interested}


@api_router.get("/")
async def root():
    return {"message": "PhD Outreach Agent API"}


app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
