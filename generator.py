import json, re
import anthropic
from config import MODEL, LEVEL_HINTS

PROMPT = """You are an expert Arabic vocabulary teacher creating one Instagram post for Urdu/English speakers.

Level: {level} -> {hint}
Do NOT repeat any of these already-posted words: {used}

Pick ONE Arabic word (a single word, not a phrase). Only the meaning matters, no grammar.
Return ONLY valid JSON, no markdown, with exactly these keys:
{{
  "arabic": "word with full tashkeel/harakat",
  "transliteration": "simple Latin pronunciation e.g. kitaab",
  "english": "concise meaning, 1-4 words",
  "urdu": "concise meaning in Urdu script, 1-4 words, natural and correct",
  "hook": "one short, curious, engaging caption first line (a question or challenge), with 1 emoji",
  "hashtags": ["5 relevant hashtags without the # sign, mix of niche and broad"]
}}
Accuracy of the meanings is critical."""

def generate_word(level: str, used: list[str], retries: int = 3) -> dict:
    client = anthropic.Anthropic()
    plain = lambda s: re.sub(r"[\u064B-\u065F\u0670]", "", s).strip()
    used_plain = {plain(u) for u in used}
    for _ in range(retries):
        msg = client.messages.create(
            model=MODEL, max_tokens=600,
            messages=[{"role": "user", "content": PROMPT.format(
                level=level, hint=LEVEL_HINTS[level], used=", ".join(used[-400:]) or "none")}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        try:
            data = json.loads(text)
            assert all(data.get(k) for k in ("arabic", "transliteration", "english", "urdu", "hook", "hashtags"))
        except Exception:
            continue
        if plain(data["arabic"]) in used_plain:
            continue
        return data
    raise RuntimeError("Could not generate a valid unique word")

def build_caption(w: dict, level: str, handle: str) -> str:
    tags = " ".join("#" + t.lstrip("#").replace(" ", "") for t in w["hashtags"][:5])
    return (
        f"{w['hook']}\n\n"
        f"📖 {w['arabic']} ({w['transliteration']})\n"
        f"🇬🇧 {w['english']}\n"
        f"🇵🇰 {w['urdu']}\n"
        f"📊 Level: {level}\n\n"
        f"💾 Save this so you never forget it\n"
        f"📩 Send to a friend learning Arabic\n"
        f"💬 Did you already know it? Tell me below!\n"
        f"➕ Follow {handle} for a new Arabic word every day\n\n"
        f"{tags} #arabic #learnarabic #urdu"
    )
