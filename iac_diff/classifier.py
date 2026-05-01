from groq import Groq
import json
import os
import time

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are a DevSecOps expert analyzing Terraform infrastructure changes.
For each change, return ONLY valid JSON with these fields:
- intent: one sentence describing what this change does
- risk_level: one of "none", "low", "medium", "high", "critical"
- risk_reason: one sentence explaining the risk (or "No significant risk" if none)
- security_flags: list of strings e.g. ["opens_port_22", "public_ip", "iam_privilege_escalation"]
Return only raw JSON. No markdown, no backticks, no explanation."""


def classify_change(change, blast) -> dict:
    user_msg = f"""
Resource: {change.resource_id} (type: {change.resource_type})
Change type: {change.change_type}
Changed fields: {change.changed_keys}
Before config: {json.dumps(change.before, indent=2, default=str)}
After config: {json.dumps(change.after, indent=2, default=str)}
Blast radius: affects {blast.affected_count()} downstream resources: {blast.directly_affected[:5]}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.1,
            max_tokens=400
        )
        text = response.choices[0].message.content.strip()
        text = text.removeprefix("```json").removesuffix("```").strip()
        return json.loads(text)
    except Exception as e:
        return {
            "intent": "Unable to classify",
            "risk_level": "unknown",
            "risk_reason": str(e)[:80],
            "security_flags": []
        }


def classify_all(blast_results: list) -> list[dict]:
    results = []
    for r in blast_results:
        print(f"  Classifying {r.change.resource_id}...")
        results.append(classify_change(r.change, r))
        time.sleep(1)
    return results