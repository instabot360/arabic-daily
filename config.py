import os

HANDLE = os.getenv("IG_HANDLE", "@yourhandle")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

# (level name, number of days at that level). None = forever.
CURRICULUM = [
    ("Beginner", 60),
    ("Elementary", 60),
    ("Intermediate", 90),
    ("Advanced", 90),
    ("Expert", None),
]

LEVEL_HINTS = {
    "Beginner": "very common everyday words (nouns, simple verbs, colors, family, food, greetings)",
    "Elementary": "common words used in daily conversation, travel, work, feelings",
    "Intermediate": "words from news, education, religion, society; slightly abstract concepts",
    "Advanced": "formal, literary and academic vocabulary; less common but real words",
    "Expert": "classical, eloquent and rare vocabulary found in literature, poetry and Quranic/classical texts",
}

def level_for_day(day: int) -> str:
    total = 0
    for name, length in CURRICULUM:
        if length is None:
            return name
        total += length
        if day < total:
            return name
    return CURRICULUM[-1][0]
