import os
import time
import requests

API = os.getenv("IG_API_BASE", "https://graph.facebook.com/v21.0")


def _check(response):
    if not response.ok:
        raise RuntimeError(
            f"Instagram API error {response.status_code}: {response.text}"
        )
    return response.json()


def _wait(container_id, token, tries=40, delay=5):
    """
    Wait until an Instagram media container is ready.
    """

    last_status = None

    for attempt in range(1, tries + 1):
        response = requests.get(
            f"{API}/{container_id}",
            params={
                "fields": "status_code",
                "access_token": token,
            },
            timeout=30,
        )

        data = _check(response)
        status = data.get("status_code")
        last_status = status

        print(
            f"Container {container_id}: "
            f"{status} ({attempt}/{tries})"
        )

        if status == "FINISHED":
            # Give Instagram a few extra seconds after processing
            # before attempting to publish.
            time.sleep(5)
            return

        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(
                f"Container {container_id} status: {status}"
            )

        time.sleep(delay)

    raise RuntimeError(
        f"Timed out waiting for Instagram to process media "
        f"{container_id}. Last status: {last_status}"
    )


def _publish(container_id, user_id, token, tries=8, delay=10):
    """
    Publish an Instagram media container.

    Instagram can occasionally return:
        code 9007
        subcode 2207027
        Media ID is not available

    even after the container reports FINISHED.
    Retry that specific temporary condition.
    """

    for attempt in range(1, tries + 1):
        response = requests.post(
            f"{API}/{user_id}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": token,
            },
            timeout=60,
        )

        if response.ok:
            return response.json()["id"]

        try:
            error_data = response.json().get("error", {})
        except Exception:
            error_data = {}

        error_code = error_data.get("code")
        error_subcode = error_data.get("error_subcode")

        # Instagram sometimes needs additional processing time.
        if error_code == 9007 and error_subcode == 2207027:
            print(
                f"Media {container_id} is not ready yet. "
                f"Retrying publish ({attempt}/{tries})..."
            )
            time.sleep(delay)
            continue

        # Any other error should fail immediately.
        raise RuntimeError(
            f"Instagram API error {response.status_code}: "
            f"{response.text}"
        )

    raise RuntimeError(
        f"Instagram media {container_id} could not be published "
        f"after {tries} attempts."
    )


def post_carousel(image_urls, caption, user_id, token):
    """
    Create and publish an Instagram carousel.
    """

    children = []

    # ---------------------------------------------------------
    # Create child image containers
    # ---------------------------------------------------------
    for url in image_urls:
        response = requests.post(
            f"{API}/{user_id}/media",
            data={
                "image_url": url,
                "is_carousel_item": "true",
                "access_token": token,
            },
            timeout=60,
        )

        data = _check(response)
        children.append(data["id"])

    if not children:
        raise RuntimeError("No carousel images were provided.")

    # ---------------------------------------------------------
    # Wait for every child image to finish processing
    # ---------------------------------------------------------
    for child_id in children:
        _wait(child_id, token)

    # ---------------------------------------------------------
    # Create the carousel container
    # ---------------------------------------------------------
    response = requests.post(
        f"{API}/{user_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )

    parent_id = _check(response)["id"]

    # ---------------------------------------------------------
    # Wait for the carousel itself to finish processing
    # ---------------------------------------------------------
    _wait(parent_id, token)

    # ---------------------------------------------------------
    # Publish carousel
    # ---------------------------------------------------------
    return _publish(parent_id, user_id, token)


def post_reel(video_url, caption, user_id, token, cover_url=None):
    """
    Create and publish an Instagram Reel.
    """

    data = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": token,
    }

    if cover_url:
        data["cover_url"] = cover_url

    # ---------------------------------------------------------
    # Create Reel container
    # ---------------------------------------------------------
    response = requests.post(
        f"{API}/{user_id}/media",
        data=data,
        timeout=60,
    )

    container_id = _check(response)["id"]

    # ---------------------------------------------------------
    # Wait for Reel processing
    # Reels can take longer than images.
    # 72 × 5 seconds = 6 minutes maximum.
    # ---------------------------------------------------------
    _wait(
        container_id,
        token,
        tries=72,
        delay=5,
    )

    # ---------------------------------------------------------
    # Publish Reel
    # ---------------------------------------------------------
    return _publish(container_id, user_id, token)
