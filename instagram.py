import os, time, requests

API = os.getenv("IG_API_BASE", "https://graph.facebook.com/v21.0")

def _check(r):
    if not r.ok:
        raise RuntimeError(f"Instagram API error {r.status_code}: {r.text}")
    return r.json()

def _wait(container_id, token, tries=30):
    for _ in range(tries):
        st = _check(requests.get(f"{API}/{container_id}", params={
            "fields": "status_code", "access_token": token}, timeout=30)).get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {container_id} status {st}")
        time.sleep(5)
    raise RuntimeError("Timed out waiting for Instagram to process media")

def post_carousel(image_urls, caption, user_id, token):
    children = []
    for url in image_urls:
        r = _check(requests.post(f"{API}/{user_id}/media", data={
            "image_url": url, "is_carousel_item": "true", "access_token": token}, timeout=60))
        children.append(r["id"])
    for c in children:
        _wait(c, token)
    parent = _check(requests.post(f"{API}/{user_id}/media", data={
        "media_type": "CAROUSEL", "children": ",".join(children),
        "caption": caption, "access_token": token}, timeout=60))["id"]
    _wait(parent, token)
    return _check(requests.post(f"{API}/{user_id}/media_publish", data={
        "creation_id": parent, "access_token": token}, timeout=60))["id"]
