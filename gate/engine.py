"""Pure batch evaluation: no network, mutations of input, or model calls."""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import re
from urllib.parse import urlparse

from .policies import content_issues, normalize
from .validation import validate_inputs

DEFAULT_NOW = datetime(2026, 10, 13, 9, tzinfo=timezone.utc)
KINDS = ("statics", "videos")


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamps must include a timezone")
    return result.astimezone(timezone.utc)


def business_due(start: date, days: int) -> date:
    if type(days) is not int or days < 0:
        raise ValueError("Business days must be a non-negative integer")
    while days:
        start += timedelta(days=1)
        if start.weekday() < 5:
            days -= 1
    return start


def product_key(value: str) -> str:
    return re.sub(r"^(?:the|a|an)\s+", "", normalize(value))


def approval(brief: dict, client: dict, kind: str, now: datetime) -> dict | None:
    """Latest explicit lead decision wins. Scope is this brief, never the client.

    Author fields are trusted fixture identities; production must use ClickUp IDs.
    """
    decisions = []
    for comment in brief.get("comments", []):
        try:
            at = timestamp(comment["at"])
        except (KeyError, ValueError, TypeError):
            continue
        if comment.get("by") != client["squad_lead"] or not timestamp(brief["created_at"]) <= at <= now:
            continue
        text = normalize(comment.get("text", ""))
        if not re.search(rf"\b{kind}\b", text):
            continue
        if re.search(r"\b(not approved|denied|revoked|rejected|cancelled)\b", text):
            decisions.append((at, None))
        elif "?" not in text and not re.search(r"\b(if|pending|unless|subject to)\b", text) and re.match(rf"^{kind}\s+(?:is\s+)?(?:approved|ok)\b", text):
            # Explicit quantities, when supplied, must cover the requested type/count.
            scopes = re.findall(r"\b(\d+)\s+(video|static)s?\b", text)
            if scopes:
                allowed = {k + "s": int(n) for n, k in scopes}
                if any(brief["deliverables"].get(k, 0) > allowed.get(k, 0) for k in KINDS):
                    decisions.append((at, None))
                    continue
            decisions.append((at, comment))
    return sorted(decisions, key=lambda item: item[0])[-1][1] if decisions else None


def evaluate_batch(briefs: list[dict], clients: list[dict], now: datetime = DEFAULT_NOW) -> dict:
    validate_inputs(briefs, clients)
    if now.tzinfo is None:
        raise ValueError("Check time must include a timezone")
    now = now.astimezone(timezone.utc)
    ids = [b["id"] for b in briefs]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate brief IDs: refusing ambiguous quota reservations")
    lookup = {c["client"]: c for c in clients}
    if len(lookup) != len(clients):
        raise ValueError("Duplicate client names")
    usage = {name: deepcopy(c["used_this_month"]) for name, c in lookup.items()}
    results = []
    for b in sorted(briefs, key=lambda item: (timestamp(item["created_at"]), item["id"])):
        issues = []
        def block(code, evidence, action):
            issues.append({"code": code, "evidence": evidence, "action": action})
        client = lookup.get(b.get("client"))
        if client is None:
            block("UNKNOWN_CLIENT", "Client not found in configuration.", "Please confirm the client account for this brief.")
        resolved = []
        approved = {}
        before = deepcopy(usage.get(b.get("client"), {}))
        counts = b.get("deliverables", {})
        valid_counts = isinstance(counts, dict) and set(counts) == set(KINDS) and all(type(counts.get(k)) is int and counts[k] >= 0 for k in KINDS)
        if not valid_counts or sum(counts.values()) == 0:
            block("DELIVERABLES", "Counts must be non-negative integers with at least one deliverable.", "Please specify static and video counts, with at least one deliverable.")
        if not b.get("platforms") or any(not isinstance(p, str) or not p.strip() for p in b["platforms"]):
            block("PLATFORMS", "No valid platform supplied.", "Please confirm the target platform(s).")
        formats = b.get("formats", [])
        if not formats or any(not re.fullmatch(r"[1-9]\d*:[1-9]\d*(?:\s+[1-9]\d*s)?", f) for f in formats):
            block("FORMATS", "Formats need a positive aspect ratio, optionally followed by duration (e.g. 9:16 15s).", "Please specify the aspect ratio for each format.")
        if valid_counts and counts["videos"] and (not formats or not any(re.search(r"\s[1-9]\d*s$", f) for f in formats)):
            block("VIDEO_DURATION", "Video requested without a duration.", "Please specify video duration, for example 9:16 15s.")
        elif valid_counts and counts["videos"] and not counts["statics"] and any(not re.search(r"\s[1-9]\d*s$", f) for f in formats):
            block("VIDEO_DURATION", "At least one video format is missing a duration.", "Please specify a duration for every video format.")
        try:
            due = date.fromisoformat(b.get("due_date", ""))
        except (ValueError, TypeError):
            due = None
            block("DUE_DATE", "Missing or invalid due date.", "Please confirm a valid due date (YYYY-MM-DD).")
        url = urlparse(b.get("assets_link", ""))
        # Only an explicit positive instruction can substitute for the flag.
        # Do not interpret "do not use Studio catalog" as an asset source.
        notes = normalize(b.get("notes", ""))
        studio_instruction = bool(re.search(r"(?:^|[.!;]\s*)(?:please\s+)?use\s+(?:the\s+)?(?:packshots (?:already )?in (?:the )?)?studio catalog\b", notes))
        studio_conflict = bool(re.search(r"\b(?:not|never|avoid|don't)\b[^.!;]*\bstudio catalog\b", notes))
        studio = (b.get("use_studio_catalog") is True or studio_instruction) and not studio_conflict
        if not (url.scheme == "https" and url.hostname == "drive.google.com" and url.path not in ("", "/")) and not studio:
            block("ASSETS", "Neither a Google Drive asset link nor Studio catalog instruction is present.", "Please share the Drive assets folder or confirm use of Studio catalog shots.")
        if not b.get("products"):
            block("PRODUCTS", "No products specified.", "Please specify the products, or 'brand' for brand-only work.")
        if timestamp(b["created_at"]) > now:
            block("FUTURE_BRIEF", "Brief was created after the check time.", "We need to verify the brief timestamp before scheduling production.")
        if client:
            if client["status"] != "active":
                block("CLIENT_PAUSED", "Client account is not active.", "Production is currently paused; we will coordinate account reactivation before scheduling this work.")
            for kind in ("rush", "overage"):
                found = approval(b, client, kind, now) if valid_counts else None
                if found:
                    approved[kind] = deepcopy(found)
            if due and valid_counts:
                earliest = business_due(now.date(), 5 if counts["videos"] else 3)
                if due < now.date():
                    block("TURNAROUND", f"Due {due} is already in the past; rush approval cannot fix a past deadline.", f"Please confirm a new due date; the earliest standard date is {earliest}.")
                elif due < earliest and "rush" not in approved:
                    block("TURNAROUND", f"Due {due}; earliest standard date is {earliest}. No applicable rush approval.", f"Please move the due date to {earliest} or later; for an earlier feasible date, we need rush approval from {client['squad_lead']}.")
            for requested in b.get("products", []):
                if product_key(requested) == "brand":
                    resolved.append("brand")
                    continue
                matches = [p for p in client["catalog"] if product_key(requested) in {product_key(x) for x in [p["sku"], p["name"], *p.get("aliases", [])]}]
                if len(matches) != 1:
                    block("UNKNOWN_PRODUCT", f"Product '{requested}' has {len(matches)} catalog matches.", f"Please confirm an active catalog SKU for '{requested}'.")
                elif not matches[0]["active"]:
                    block("INACTIVE_PRODUCT", f"{matches[0]['sku']} is discontinued or inactive.", f"Please replace '{requested}' with an active product.")
                else:
                    resolved.append(matches[0]["sku"])
            for code, evidence, action in content_issues(b, client):
                block(code, evidence, action)
            if valid_counts:
                for k in KINDS:
                    projected = before[k] + counts[k]
                    if counts[k] and projected > client["plan_per_month"][k] and "overage" not in approved:
                        block("QUOTA", f"{k}: {before[k]} already used/reserved + {counts[k]} requested = {projected}, above plan {client['plan_per_month'][k]}.", f"This request exceeds the remaining allowance for {k}. Please reduce or defer that quantity, or arrange an overage approved by {client['squad_lead'].rstrip('.')}.")
        passed = not issues
        if passed:
            for k in KINDS:
                usage[b["client"]][k] += counts[k]
        actions = list(dict.fromkeys(i["action"] for i in issues))
        message = None if passed else (f"Hi {b.get('client', 'there')} team — before we can schedule brief {b['id']}, please help us resolve the following:\n\n" + "\n".join(f"- {a}" for a in actions) + "\n\nWe will recheck the updated brief before confirming production.")
        results.append({"id": b["id"], "client": b.get("client"), "status": "PASS" if passed else "BLOCKED", "owner": client["squad_lead"] if client else "Operations", "resolved_products": resolved, "issues": issues, "approvals": approved, "usage_before": before, "usage_after": deepcopy(usage.get(b.get("client"), {})), "clarification_message": message})
    return {"checked_at": now.isoformat(), "policy_version": "1.0", "summary": {"total": len(results), "passed": sum(r["status"] == "PASS" for r in results), "blocked": sum(r["status"] == "BLOCKED" for r in results)}, "results": results, "final_usage": usage}
