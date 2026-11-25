from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Akshara AI Operations Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BRANCHES = [
    {"id": "br-01", "code": "AKSH-B01", "name": "Branch 01 (Placeholder)", "status": "Pending Official Name"},
    {"id": "br-02", "code": "AKSH-B02", "name": "Branch 02 (Placeholder)", "status": "Pending Official Name"},
    {"id": "br-03", "code": "AKSH-B03", "name": "Branch 03 (Placeholder)", "status": "Pending Official Name"},
    {"id": "br-04", "code": "AKSH-B04", "name": "Branch 04 (Placeholder)", "status": "Pending Official Name"},
    {"id": "br-05", "code": "AKSH-B05", "name": "Branch 05 (Placeholder)", "status": "Pending Official Name"},
    {"id": "br-06", "code": "AKSH-B06", "name": "Branch 06 (Placeholder)", "status": "Pending Official Name"},
    {"id": "br-07", "code": "AKSH-B07", "name": "Branch 07 (Placeholder)", "status": "Pending Official Name"},
    {"id": "br-08", "code": "AKSH-POCH", "name": "Pocharam Branch", "status": "Configured Branch"},
]

TICKETS: list[dict] = []


class TicketCreate(BaseModel):
    branch_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=3000)


def _suggest_triage(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()
    if "cctv" in text or "camera" in text:
        return {"category": "CCTV", "priority": "HIGH", "confidence": 0.89, "requires_human_review": True, "is_suggestion_only": True}
    if "password" in text or "login" in text or "account" in text:
        return {"category": "ACCOUNT_ACCESS", "priority": "HIGH", "confidence": 0.86, "requires_human_review": True, "is_suggestion_only": True}
    if "wifi" in text or "network" in text or "internet" in text:
        return {"category": "NETWORK", "priority": "HIGH", "confidence": 0.88, "requires_human_review": False, "is_suggestion_only": True}
    if "projector" in text or "panel" in text or "smartboard" in text:
        return {"category": "CLASSROOM_TECHNOLOGY", "priority": "MEDIUM", "confidence": 0.90, "requires_human_review": False, "is_suggestion_only": True}
    return {"category": "HARDWARE", "priority": "MEDIUM", "confidence": 0.68, "requires_human_review": True, "is_suggestion_only": True}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "akshara-ai-ops",
        "branches": len(BRANCHES),
        "includes_pocharam": True,
    }


@app.get("/branches")
def list_branches(
    x_role: str = Header(default="CENTRAL_IT_ADMIN", alias="X-Role"),
    x_branch_id: str = Header(default="", alias="X-Branch-Id"),
    x_active: str = Header(default="true", alias="X-Active"),
):
    if x_active.lower() != "true":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if x_role == "CENTRAL_IT_ADMIN":
        return BRANCHES
    return [b for b in BRANCHES if b["id"] == x_branch_id]


@app.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    x_role: str = Header(default="BRANCH_STAFF", alias="X-Role"),
    x_branch_id: str = Header(default="br-08", alias="X-Branch-Id"),
    x_active: str = Header(default="true", alias="X-Active"),
):
    if x_active.lower() != "true":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    valid_ids = {b["id"] for b in BRANCHES}
    if payload.branch_id not in valid_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")
    if x_role != "CENTRAL_IT_ADMIN" and payload.branch_id != x_branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Branch access denied")

    suggestion = _suggest_triage(payload.title, payload.description)
    now = datetime.now(timezone.utc).isoformat()
    ticket = {
        "id": f"tkt-{len(TICKETS) + 1:04d}",
        "branch_id": payload.branch_id,
        "title": payload.title,
        "description": payload.description,
        "category": suggestion["category"],
        "priority": suggestion["priority"],
        "status": "NEW",
        "ai_suggestion": suggestion,
        "created_at": now,
    }
    TICKETS.append(ticket)
    return ticket


@app.get("/tickets")
def list_tickets(
    x_role: str = Header(default="CENTRAL_IT_ADMIN", alias="X-Role"),
    x_branch_id: str = Header(default="", alias="X-Branch-Id"),
    x_active: str = Header(default="true", alias="X-Active"),
):
    if x_active.lower() != "true":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if x_role == "CENTRAL_IT_ADMIN":
        return TICKETS
    return [t for t in TICKETS if t["branch_id"] == x_branch_id]