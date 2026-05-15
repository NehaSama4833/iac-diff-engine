import json
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

app = FastAPI(title="Terraform Semantic Diff Engine")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Plug your real diff engine here.
# The stub below returns a realistic structure so the UI can be developed
# independently.  Replace `_run_semantic_diff` with your actual logic.
# ---------------------------------------------------------------------------

def _run_semantic_diff(before: str, after: str) -> dict:
    """
    Replace this stub with your actual semantic diff engine.

    Expected return shape:
    {
        "risk_level":    "low" | "medium" | "high" | "critical",
        "blast_radius":  str,          # e.g. "3 resources affected"
        "intent":        str,          # human-readable summary
        "security_flags": list[str],   # list of flag descriptions
        "report":        str,          # rich markdown / plain-text report
        "changes":       list[dict],   # optional structured change list
    }
    """
    # ---- stub logic (delete and wire your engine) ----
    added   = len([l for l in after.splitlines()   if l.strip() and l not in before.splitlines()])
    removed = len([l for l in before.splitlines()  if l.strip() and l not in after.splitlines()])
    total   = added + removed

    risk = "low"
    if total > 40:
        risk = "critical"
    elif total > 20:
        risk = "high"
    elif total > 8:
        risk = "medium"

    flags = []
    sensitive = ["password", "secret", "token", "key", "credentials", "private"]
    for word in sensitive:
        if word in after.lower() and word not in before.lower():
            flags.append(f"Newly introduced sensitive identifier: `{word}`")

    if "0.0.0.0/0" in after and "0.0.0.0/0" not in before:
        flags.append("Wide-open ingress rule added (0.0.0.0/0)")

    report_lines = [
        "## Semantic Diff Report",
        "",
        f"**Lines added:** {added}   **Lines removed:** {removed}",
        "",
        "### Change Summary",
        "The diff engine stub detected structural changes between the two configurations.",
        "Wire `_run_semantic_diff` in `app.py` to your real engine for production results.",
        "",
    ]
    if flags:
        report_lines += ["### Security Observations", ""] + [f"- {f}" for f in flags]

    return {
        "risk_level":     risk,
        "blast_radius":   f"{max(1, total // 5)} resource(s) potentially affected",
        "intent":         f"Configuration updated with {added} addition(s) and {removed} removal(s). "
                          "Connect your semantic engine for a deeper intent summary.",
        "security_flags": flags,
        "report":         "\n".join(report_lines),
        "changes": [
            {"type": "added",   "count": added},
            {"type": "removed", "count": removed},
        ],
    }
    # ---- end stub ----


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze(
    before: UploadFile = File(..., description="Original Terraform file"),
    after:  UploadFile = File(..., description="Modified Terraform file"),
):
    for f in (before, after):
        if not f.filename.endswith(".tf"):
            raise HTTPException(
                status_code=400,
                detail=f"'{f.filename}' is not a .tf file. Please upload valid Terraform files.",
            )

    try:
        before_text = (await before.read()).decode("utf-8")
        after_text  = (await after.read()).decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Files must be UTF-8 encoded text.")

    if not before_text.strip() or not after_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded files must not be empty.")

    try:
        result = _run_semantic_diff(before_text, after_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Diff engine error: {exc}")

    return result
