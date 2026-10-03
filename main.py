"""Daily Arabic word -> Instagram carousel.

  python main.py prepare [--demo]   pick word, render slides, write posts/<date>/post.json
  python main.py publish [--dry]    post the newest unposted post to Instagram
"""
import datetime, json, os, sys, time
import requests
from config import HANDLE
import render, instagram

STATE = "state.json"

def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"day": 0}

def save_state(s):
    json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=2)

def raw_url(rel_path):
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.getenv("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{rel_path}"

def prepare(demo=False):
    from generator import word_for_day, build_caption
    state = load_state()
    day = 1 if demo else state["day"] + 1
    w = word_for_day(day)
    level = w["level"]
    date = datetime.date.today().isoformat()
    out = os.path.join("posts", date)
    render.render_post(w, level, day, HANDLE, out)
    post = {"date": date, "day": day, "level": level, "word": w,
            "caption": build_caption(w, day, HANDLE),
            "images": [f"{out}/slide_{i}.jpg" for i in (1, 2, 3)], "posted": False}
    json.dump(post, open(os.path.join(out, "post.json"), "w"), ensure_ascii=False, indent=2)
    if not demo:
        save_state({"day": day})
    print(f"Prepared day {day} [{level}]: {w['arabic']} = {w['english']} / {w['urdu']}")

def latest_pending():
    if not os.path.isdir("posts"):
        return None
    for d in sorted(os.listdir("posts"), reverse=True):
        p = os.path.join("posts", d, "post.json")
        if os.path.exists(p):
            post = json.load(open(p))
            if not post["posted"]:
                return p, post
    return None

def wait_public(urls, tries=24):
    for u in urls:
        for _ in range(tries):
            if requests.head(u, timeout=15).status_code == 200:
                break
            time.sleep(5)
        else:
            raise RuntimeError(f"Image not publicly reachable: {u}")

def publish(dry=False):
    found = latest_pending()
    if not found:
        print("Nothing to publish.")
        return
    path, post = found
    print(post["caption"])
    if dry:
        return
    urls = [raw_url(p) for p in post["images"]]
    wait_public(urls)
    media_id = instagram.post_carousel(urls, post["caption"],
                                       os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"])
    post["posted"], post["media_id"] = True, media_id
    json.dump(post, open(path, "w"), ensure_ascii=False, indent=2)
    print("Published, media id:", media_id)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prepare":
        prepare("--demo" in sys.argv)
    elif cmd == "publish":
        publish("--dry" in sys.argv)
    else:
        print(__doc__)
