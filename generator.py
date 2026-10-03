"""No-AI word source: reads words.txt (Level|Arabic|Transliteration|English|Urdu)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

HOOKS = {
    "Beginner": ["Can you guess this Arabic word? 🤔", "Do you already know this word? 👀",
                 "A word you'll use all the time ✨", "Quick challenge: what does this mean? 🧠"],
    "Elementary": ["Level up your Arabic today 📈", "You may have heard this one before 👂",
                   "Can you guess it before swiping? 🤔", "Everyday Arabic, one word at a time ✨"],
    "Intermediate": ["Do you know this word? Be honest 😅", "A word that makes you sound fluent 💬",
                     "Test your Arabic: what does this mean? 🧠", "Time to stretch your vocabulary 💪"],
    "Advanced": ["Only strong learners know this one 🔥", "Think you know it? Swipe to check 🧐",
                 "An advanced word for serious learners 📚", "Can you get this without help? 💪"],
    "Expert": ["Rare and beautiful Arabic ✨", "Real Arabic mastery: do you know this one? 🏆",
               "A word from classical Arabic 📜", "Very few learners know this word 👑"],
}
TAGS = ["arabicwords", "arabicvocabulary", "arabiclanguage", "learnurdu", "urdu", "wordoftheday",
        "arabicforbeginners", "arabiclearning", "languagelearning", "arabicquotes", "urduvocabulary", "dailyarabic"]

def load_words(path=None):
    path = path or os.path.join(HERE, "words.txt")
    words = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) != 5:
            raise ValueError(f"words.txt line has {len(p)} parts, expected 5: {line}")
        words.append(dict(level=p[0], arabic=p[1], transliteration=p[2], english=p[3], urdu=p[4]))
    return words

def word_for_day(day: int) -> dict:
    words = load_words()
    if day > len(words):
        raise SystemExit(f"OUT OF WORDS: day {day} but words.txt only has {len(words)} words. "
                         f"Add more lines to the bottom of words.txt.")
    return words[day - 1]

def hook_for(level, day):
    hooks = HOOKS.get(level, HOOKS["Beginner"])
    return hooks[day % len(hooks)]

def build_caption(w, day, handle):
    tags = ["learnarabic", "arabic"] + [TAGS[(day * 3 + i) % len(TAGS)] for i in range(4)]
    tags = " ".join("#" + t for t in dict.fromkeys(tags))
    return (
        f"{hook_for(w['level'], day)}\n\n"
        f"📖 {w['arabic']} ({w['transliteration']})\n"
        f"🇬🇧 {w['english']}\n"
        f"🇵🇰 {w['urdu']}\n"
        f"📊 Level: {w['level']}\n\n"
        f"💾 Save this so you never forget it\n"
        f"📩 Send to a friend learning Arabic\n"
        f"💬 Did you already know it? Tell me below!\n"
        f"➕ Follow {handle} for a new Arabic word every day\n\n"
        f"{tags}"
    )
