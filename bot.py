import os
import random
import shutil
from pathlib import Path
import base64
import subprocess
from dotenv import load_dotenv
from google import genai

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# SETTINGS
# ============================================================


SHORTS_FOLDER = Path("shorts")
UPLOADED_FOLDER = Path("uploaded")

CLIENT_SECRET = "client_secret.json"
TOKEN_FILE = "youtube_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_HANDLE = os.getenv("TARGET_HANDLE")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from .env"
    )

if not TARGET_HANDLE:
    raise RuntimeError(
        "TARGET_HANDLE is missing from .env"
    )

# ============================================================
# VIDEO FORMAT
# ============================================================

def get_video_dimensions(video_path):
    """Return (width, height) using FFprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            str(video_path)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    width, height = map(int, result.stdout.strip().split("x"))
    return width, height


def prepare_video(video_path):
    """
    If the video is horizontal, create a 1080x1920 9:16 version
    with a blurred enlarged background and the complete original
    video centered on top.

    Vertical/square videos are returned unchanged.

    Returns:
        (video_to_use, temporary_video)
    """
    width, height = get_video_dimensions(video_path)

    print(f"📐 Video size: {width}x{height}")

    if width <= height:
        print("✅ Video is already vertical/square.")
        print("➡️ Using original video.")
        return video_path, None

    print("↔️ Horizontal video detected!")
    print("🌀 Converting to 9:16 with blurred background...")

    temp_folder = Path("processed")
    temp_folder.mkdir(exist_ok=True)

    output_path = temp_folder / f"{video_path.stem}_vertical.mp4"

    filter_complex = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "boxblur=25:10[blurred];"
        "[fg]scale=1080:1920:force_original_aspect_ratio=decrease"
        "[foreground];"
        "[blurred][foreground]overlay=(W-w)/2:(H-h)/2,"
        "format=yuv420p[v]"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg/FFprobe was not found. Make sure ffmpeg and ffprobe "
            "are available in Command Prompt."
        )

    print(f"✅ Vertical version created: {output_path}")

    return output_path, output_path


# ============================================================
# GEMINI
# ============================================================

gemini = genai.Client(
    api_key=GEMINI_API_KEY
)


def generate_metadata(video_path):

    print("\n🤖 Reading the entire video with Gemini...")

    # Gemini analyzes the SAME final video that will be uploaded.
    video_bytes = video_path.read_bytes()

    # Gemini inline requests should stay below the request-size limit.
    # Your current Shorts are only a few MB, so this is ideal.
    if len(video_bytes) > 18 * 1024 * 1024:
        raise RuntimeError(
            "Video is too large for inline Gemini analysis. "
            "Keep Shorts below about 18 MB for this version."
        )

    video = base64.b64encode(video_bytes).decode("ascii")

    prompt = """
You are the metadata generator for a YouTube Shorts meme channel.

WATCH AND ANALYZE THE ENTIRE VIDEO carefully before writing anything.

Generate metadata based ONLY on what actually happens in the video.

STYLE:

TITLE:
- Catchy
- Funny
- Relatable when appropriate
- Gen-Z / meme style
- Usually 5–12 words
- Use 1–3 emojis
- Make people curious
- NEVER falsely describe the video

DESCRIPTION:
- Short and entertaining
- Use POV when appropriate
- Use reaction/dialogue lines when appropriate
- Natural meme style
- Do NOT sound like an SEO article
- Finish with relevant hashtags
- Include #shorts

TAGS:
- 20–30 relevant tags
- Mix specific + broad + long-tail keywords
- Comma separated
- NO # symbols
- NO unrelated keywords
- Keep the entire tag string below 500 characters

Example style:

TITLE:
Family Vacations ALWAYS End Like This 💀🐱

DESCRIPTION:
POV: You survived 4 hours in the car with your family 😭💀

SIS: 😐
ME: 🗿
BRO: 😡

Every. Single. Time. 😂🐱

#catmemes #familyvacation #relatable #funny #meme #cats #shorts

TAGS:
family vacation, family vacation meme, family memes, family trip, vacation meme, relatable meme, cat meme, cat memes, funny cats, funny meme, meme, memes, siblings, sibling meme, brother sister meme, family trip meme, road trip meme, car ride meme, relatable, funny shorts, meme shorts, cat shorts

IMPORTANT:
Return ONLY this exact format:

TITLE:
<title>

DESCRIPTION:
<description>

TAGS:
<tag1, tag2, tag3>
"""

    print("🧠 Gemini is watching the entire video...")

    interaction = gemini.interactions.create(
        model="gemini-3.6-flash",
        input=[
            {
                "type": "video",
                "data": video,
                "mime_type": "video/mp4"
            },
            {
                "type": "text",
                "text": prompt
            }
        ]
    )

    result = interaction.output_text

    if not result:
        raise RuntimeError(
            "Gemini returned empty metadata."
        )

    print("✅ Metadata generated.")

    return parse_metadata(result)


# ============================================================
# PARSE GEMINI
# ============================================================

def parse_metadata(text):

    text = text.strip()

    if "TITLE:" not in text:
        raise RuntimeError(
            "Gemini response has no TITLE."
        )

    if "DESCRIPTION:" not in text:
        raise RuntimeError(
            "Gemini response has no DESCRIPTION."
        )

    if "TAGS:" not in text:
        raise RuntimeError(
            "Gemini response has no TAGS."
        )

    title = (
        text.split("TITLE:", 1)[1]
        .split("DESCRIPTION:", 1)[0]
        .strip()
    )

    description = (
        text.split("DESCRIPTION:", 1)[1]
        .split("TAGS:", 1)[0]
        .strip()
    )

    tags = (
        text.split("TAGS:", 1)[1]
        .strip()
    )

    # Clean accidental markdown
    title = title.strip("*` ")

    # YouTube title maximum
    title = title[:100]

    # Clean tags
    raw_tags = [
        tag.strip()
        for tag in tags.split(",")
        if tag.strip()
    ]

    clean_tags = []
    total_length = 0

    for tag in raw_tags:

        addition = len(tag) + 1

        if total_length + addition > 500:
            break

        clean_tags.append(tag)
        total_length += addition

    tags = ", ".join(clean_tags)

    if not title:
        raise RuntimeError("Empty title.")

    if not description:
        raise RuntimeError("Empty description.")

    if not tags:
        raise RuntimeError("Empty tags.")

    return title, description, tags


# ============================================================
# YOUTUBE LOGIN
# ============================================================

def youtube_login():

    print("\n🔐 Connecting to YouTube...")

    credentials = None

    # Reuse saved login
    if Path(TOKEN_FILE).exists():

        from google.oauth2.credentials import Credentials

        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # First login
    if not credentials or not credentials.valid:

        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET,
            SCOPES
        )

        credentials = flow.run_local_server(
            port=0
        )

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token:

            token.write(
                credentials.to_json()
            )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    return youtube


# ============================================================
# CHANNEL VERIFICATION
# ============================================================

def verify_channel(youtube):

    print("\n🔎 Verifying YouTube channel...")

    # Find target channel using @handle
    target = youtube.channels().list(
        part="id,snippet",
        forHandle=TARGET_HANDLE
    ).execute()

    target_items = target.get(
        "items",
        []
    )

    if not target_items:

        raise RuntimeError(
            f"Could not find {TARGET_HANDLE}"
        )

    target_channel = target_items[0]

    target_id = target_channel["id"]

    target_name = (
        target_channel["snippet"]["title"]
    )

    print(
        f"🎯 Target channel: {target_name}"
    )

    print(
        f"🆔 Target ID: {target_id}"
    )

    # Find authenticated channel
    mine = youtube.channels().list(
        part="id,snippet",
        mine=True
    ).execute()

    mine_items = mine.get(
        "items",
        []
    )

    if not mine_items:

        raise RuntimeError(
            "Could not identify authenticated channel."
        )

    authenticated = mine_items[0]

    authenticated_id = authenticated["id"]

    authenticated_name = (
        authenticated["snippet"]["title"]
    )

    print(
        f"🔐 Logged-in channel: {authenticated_name}"
    )

    print(
        f"🆔 Logged-in ID: {authenticated_id}"
    )

    # SAFETY CHECK
    if authenticated_id != target_id:

        raise RuntimeError(
            "\n🚨 CHANNEL MISMATCH!\n"
            f"Target: {target_name}\n"
            f"Logged in: {authenticated_name}\n\n"
            "UPLOAD CANCELLED."
        )

    print(
        "\n✅ CHANNEL VERIFIED!"
    )


# ============================================================
# YOUTUBE UPLOAD
# ============================================================

def upload_video(
    youtube,
    video_path,
    title,
    description,
    tags
):

    print("\n📤 Uploading to YouTube...")

    tag_list = [
        tag.strip()
        for tag in tags.split(",")
        if tag.strip()
    ]

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tag_list,
            "categoryId": "24"
        },

        "status": {
            # FIRST TEST = PRIVATE
            "privacyStatus": "public",

            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/*",
        chunksize=8 * 1024 * 1024,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None

    while response is None:

        status, response = request.next_chunk()

        if status:

            progress = int(
                status.progress() * 100
            )

            print(
                f"📤 Upload: {progress}%"
            )

    video_id = response["id"]

    print("\n✅ UPLOAD SUCCESSFUL!")
    print(f"🎬 Video ID: {video_id}")

    return video_id


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n=================================")
    print(" 🤖 YOUTUBE SHORTS BOT")
    print("=================================\n")

    SHORTS_FOLDER.mkdir(
        exist_ok=True
    )

    UPLOADED_FOLDER.mkdir(
        exist_ok=True
    )

    videos = [
        file
        for file in SHORTS_FOLDER.iterdir()
        if file.is_file()
        and file.suffix.lower()
        in {
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm"
        }
    ]

    if not videos:

        print("📁 No videos found.")
        return

    # Random video
    video_path = random.choice(videos)

    print(
        f"🎲 Selected video: {video_path.name}"
    )

    # -----------------------------
    # PREPARE VIDEO
    # -----------------------------

    upload_path, temporary_video = prepare_video(video_path)

    # -----------------------------
    # GEMINI
    # -----------------------------

    title, description, tags = (
        generate_metadata(upload_path)
    )

    print("\n==============================")
    print("🎬 TITLE")
    print("==============================")
    print(title)

    print("\n==============================")
    print("📝 DESCRIPTION")
    print("==============================")
    print(description)

    print("\n==============================")
    print("🏷️ TAGS")
    print("==============================")
    print(tags)

    # -----------------------------
    # YOUTUBE
    # -----------------------------

    youtube = youtube_login()

    # Verify exact channel
    verify_channel(youtube)

    # Upload
    upload_video(
        youtube,
        upload_path,
        title,
        description,
        tags
    )

    # -----------------------------
    # SAFE ARCHIVE
    # -----------------------------
    # Only archive the ACTUAL file that was uploaded.
    # For horizontal videos, this is the generated vertical copy.
    # For already-vertical videos, this is the original.

    archive_source = upload_path

    destination = (
        UPLOADED_FOLDER /
        upload_path.name
    )

    if destination.exists():
        raise RuntimeError(
            f"Archive file already exists: {destination}. "
            "Upload succeeded, but the uploaded file was NOT archived."
        )

    shutil.copy2(
        str(archive_source),
        str(destination)
    )

    print(
        f"📦 Uploaded video copied to uploaded/: {destination.name}"
    )

    # For converted horizontal videos:
    # - generated vertical copy is copied to uploaded/
    # - ORIGINAL horizontal video is deleted ONLY after upload succeeds
    # - generated temporary copy is deleted from processed/
    #
    # For already-vertical videos:
    # - original is copied to uploaded/
    # - original is then deleted from shorts/ ONLY after upload succeeds

    if video_path.exists():
        video_path.unlink()

        print(
            "🗑️ Original source video deleted from shorts/."
        )

    if temporary_video and temporary_video.exists():
        temporary_video.unlink()

        print(
            "🧹 Temporary vertical copy removed."
        )

    print(
        "\n📦 Video moved to uploaded/"
    )

    print(
        "💀 MISSION COMPLETE."
    )

    print(
        "👋 Bot shutting down..."
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print("\n❌ ERROR:")
        print(error)

        print(
            "\n🛡️ Original video was NOT deleted."
        )

        input(
            "\nPress ENTER to close..."
        )