"""Daily Arabic word -> Instagram carousel.

  python main.py prepare [--demo]   pick word, render slides, write posts/<date>/post.json
  python main.py publish [--dry]    post the newest unposted post to Instagram
  python main.py reel-prepare       render a Reel of the most recently posted word
  python main.py reel-publish [--dry]
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
    date = datetime.date.today().isoformat()
    out = os.path.join("posts", date)
    meta = os.path.join(out, "post.json")
    if not demo and os.path.exists(meta):
        done = json.load(open(meta)).get("posted")
        print("Today's carousel is already posted, skipping." if done else
              "Today's post is already prepared and waiting to be published, reusing it.")
        return
    day = 1 if demo else state["day"] + 1
    w = word_for_day(day)
    level = w["level"]
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

def reel_prepare():
    import reel
    from generator import word_for_day, build_caption
    day = load_state()["day"]
    if day < 1:
        print("No carousel posted yet, skipping Reel.")
        return
    date = datetime.date.today().isoformat()
    out = os.path.join("reels", date)
    meta = os.path.join(out, "reel.json")
    if os.path.exists(meta) and json.load(open(meta)).get("posted"):
        print("Today's Reel is already posted, skipping.")
        return
    w = word_for_day(day)  # re-use the latest carousel word (no extra words consumed)
    os.makedirs(out, exist_ok=True)
    reel.render_reel(w, w["level"], day, HANDLE, os.path.join(out, "reel.mp4"))
    reel.render_cover(w, w["level"], day, HANDLE, os.path.join(out, "cover.jpg"))
    json.dump({"date": date, "day": day, "word": w, "caption": build_caption(w, day, HANDLE),
               "video": f"{out}/reel.mp4", "cover": f"{out}/cover.jpg", "posted": False},
              open(meta, "w"), ensure_ascii=False, indent=2)
    print(f"Reel prepared for day {day}: {w['arabic']} = {w['english']}")

def reel_publish(dry=False):
    if not os.path.isdir("reels"):
        print("Nothing to publish.")
        return
    for d in sorted(os.listdir("reels"), reverse=True):
        p = os.path.join("reels", d, "reel.json")
        if not os.path.exists(p):
            continue
        r = json.load(open(p))
        if r["posted"]:
            print("Latest Reel already posted.")
            return
        print(r["caption"])
        if dry:
            return
        url = raw_url(r["video"])
        cover = raw_url(r["cover"]) if r.get("cover") else None
        wait_public([u for u in (url, cover) if u])
        r["media_id"] = instagram.post_reel(url, r["caption"],
                                            os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"], cover)
        r["posted"] = True
        json.dump(r, open(p, "w"), ensure_ascii=False, indent=2)
        print("Reel published, media id:", r["media_id"])
        return
    print("Nothing to publish.")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prepare":
        prepare("--demo" in sys.argv)
    elif cmd == "publish":
        publish("--dry" in sys.argv)
    elif cmd == "reel-prepare":
        reel_prepare()
    elif cmd == "reel-publish":
        reel_publish("--dry" in sys.argv)
    else:
        print(__doc__)
