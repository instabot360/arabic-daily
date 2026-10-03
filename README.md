# Daily Arabic Word -> Instagram (fully automatic)

Every day at the scheduled time: Claude picks a new word for the current level (Beginner -> Expert over ~300 days,
never repeating), writes the caption, 3 carousel slides are rendered (word / English + Urdu meaning / follow CTA),
and the post is published to Instagram. Runs free on GitHub Actions.

## One-time setup
1. **Instagram**: convert to a Professional (Creator/Business) account and link it to a Facebook Page.
2. **Meta app**: developers.facebook.com -> create app (Business type) -> add *Instagram Graph API*.
   Generate a long-lived access token with `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`. Note your **Instagram user ID**.
3. **GitHub**: create a **public** repo (Instagram must fetch the images by URL), push this folder to it.
4. Repo -> Settings -> Secrets and variables -> Actions:
   - Secrets: `ANTHROPIC_API_KEY`, `IG_USER_ID`, `IG_ACCESS_TOKEN`
   - Variable: `IG_HANDLE` (e.g. `@arabic.daily`)
5. Actions tab -> *daily-arabic-word* -> **Run workflow** to test. Done; it now runs daily.

## Local preview (no posting)
    pip install -r requirements.txt
    python main.py prepare --demo   # renders posts/<date>/slide_*.jpg
    python main.py publish --dry    # prints the caption

## Notes
- Long-lived tokens last ~60 days: refresh before expiry (Graph API Explorer or `refresh_access_token`) and update the secret.
- Tune levels in `config.py`, post time in `daily.yml` (cron is UTC), caption format in `generator.py`.
- Growth tips: post at the same hour daily, reply to comments in the first hour, and pin a "Start here (Day 1)" post.
