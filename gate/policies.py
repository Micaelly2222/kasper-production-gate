"""Reviewed policy adapters for the supplied Brain rules, not general NLP.

New or edited Brain rules fail closed until their adapter is reviewed.
"""
import re
import unicodedata


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[-–—/]", " ", text)).strip()


def phrase_in(phrase: str, text: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(normalize(phrase)) + r"(?!\w)", normalize(text)))


SUPPORTED_RULES = {
    "Always show the can or bag, never a generic cup.": "packaging",
    "No superlatives we can't prove.": "superlatives",
    "Cosmetic, not medical: never claim to treat, cure or heal a skin condition.": "medical",
    "No before/after imagery or copy (client legal, Oct 2026).": "before_after",
    "Storm Shell is water-resistant, never 'waterproof'.": "waterproof",
    "Discounts capped at 30% (brand protection).": "discount",
    "No 'vet approved' or 'vet recommended' (no vet partnership in place).": "vet",
    "Wellness, not medical: no insomnia, cure or treatment claims.": "medical",
    "'Clinically proven' only with a linked study (none exists today).": "clinical",
    "Never show a child's face without a signed release on file.": "release",
}


def content_issues(brief: dict, client: dict) -> list[tuple[str, str, str]]:
    """Return code, evidence and English corrective action.

    Match creative fields only; comments are authorization, not proposed copy.
    Literal prohibited phrases in negated instructions require manual clarification.
    """
    issues = []
    matched_banned = set()
    fields = {k: brief.get(k, "") for k in ("title", "copy_direction", "notes")}
    text = normalize(" ".join(fields.values()))
    for phrase in client["banned_claims"]:
        for field, value in fields.items():
            if phrase_in(phrase, value):
                matched_banned.add(normalize(phrase))
                issues.append(("BANNED_CLAIM", f"{field} contains prohibited phrase '{phrase}'.",
                               f"Please remove or rephrase '{phrase}' under your brand's claims policy."))
                break
    rules = set()
    for rule in client["brain_rules"]:
        if rule not in SUPPORTED_RULES:
            issues.append(("UNREVIEWED_POLICY", f"No reviewed adapter for Brain rule: {rule}",
                           "We need our Creative Lead to review an updated brand rule before production."))
        else:
            rules.add(SUPPORTED_RULES[rule])
    if "packaging" in rules and re.search(r"\b(cup|mug)\b", text):
        negative = re.search(r"\b(?:not|never|don't|without|hide|avoid)\b[^.!;]{0,60}\b(can|bag|packaging)\b", text)
        positive = re.search(r"\b(show|include|feature|visible)\w*\b[^.!;]{0,40}\b(can|bag|packaging)\b", text)
        if negative or not positive:
            issues.append(("BRAIN_PACKAGING", "Cup-led direction does not explicitly show the branded can or bag.",
                           "Please update the visual direction to show the branded can or bag, rather than a generic cup alone."))
    if "superlatives" in rules and re.search(r"\b(best|greatest|finest|number one|unrivalled|unbeatable)\b", text):
        issues.append(("BRAIN_SUPERLATIVE", "Unsubstantiated superlative in creative direction.",
                       "Please replace the superlative with factual copy, or provide evidence for Creative Lead review."))
    # These Brain rules remain effective even if a redundant banned list changes.
    phrase_rules = {
        "waterproof": ("waterproof",),
        "vet": ("vet approved", "vet recommended"),
        "clinical": ("clinically proven",),
    }
    for rule, phrases in phrase_rules.items():
        if rule in rules:
            for phrase in phrases:
                if phrase_in(phrase, text) and normalize(phrase) not in matched_banned:
                    issues.append((f"BRAIN_{rule.upper()}", f"Brain rule prohibits '{phrase}'.",
                                   f"Please replace '{phrase}' with wording permitted by your brand rules."))
    if "medical" in rules and re.search(r"\b(treat(?:s|ing|ment)?|heal(?:s|ing)?|cur[ae](?:s|r)?|insomnia|eczema)\b", text):
        if not any(i[0] == "BANNED_CLAIM" for i in issues):
            issues.append(("BRAIN_MEDICAL", "Potential treatment or medical claim.",
                           "Please replace medical or treatment language with cosmetic or wellness wording."))
    if "before_after" in rules and re.search(r"\bbefore\s+(?:and\s+)?after\b|\bantes\s+e\s+depois\b", text):
        if not any(i[0] == "BANNED_CLAIM" for i in issues):
            issues.append(("BRAIN_BEFORE_AFTER", "Before/after concept violates the Brain.",
                           "Please use a concept without before-and-after imagery or copy."))
    if "release" in rules and re.search(r"\b(face|faces|child|children|kid|kids)\b", normalize(brief.get("copy_direction", "") + " " + brief.get("notes", ""))):
        issues.append(("RELEASE_REVIEW", "Child imagery requires a verified signed release; no release registry supplied.",
                       "Please provide the signed image release for any identifiable child, or use product-only imagery."))
    # Only percentages explicitly describing a discount are compared, not e.g. 100% cotton.
    patterns = (r"(\d+(?:\.\d+)?)\s*%\s*(?:off|discount|de desconto)",
                r"(?:discount|save|saving|desconto)\s*(?:of|de|up to)?\s*(\d+(?:\.\d+)?)\s*%")
    discounts = {float(m) for p in patterns for m in re.findall(p, text)}
    for pct in sorted(discounts):
        if pct > client["max_discount_pct"]:
            issues.append(("DISCOUNT_LIMIT", f"{pct:g}% discount exceeds {client['max_discount_pct']}% cap.",
                           f"Please reduce the discount to at most {client['max_discount_pct']}%."))
    return issues
