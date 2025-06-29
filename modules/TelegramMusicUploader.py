from telegram.ext import Application
from openai import OpenAI
from dotenv import load_dotenv
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import os
import asyncio


# === Configuration ===
load_dotenv()
BOT_TOKEN = os.getenv("tg_bot_token")
AI_TOKEN = os.getenv("openai_token")
CHAT_ID = os.getenv("chat_id")
LOG_FILE = os.getenv("LOG_FILE_PATH")
MUSIC_DIR = os.getenv("MUSIC_DIR_PATH")
SUPPORTED_EXTENSIONS = ['mp3', 'wav', 'wave', 'flac', 'aac', 'm4a', 'alac']
MAX_RETRIES = 3
TIMEOUT = 600  # 10 minutes timeout

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_TOKEN,
)


def get_new_files(directory, log_path, extensions):
    all_files = [
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
    ]

    extensions = [ext.lower() for ext in extensions]
    filtered = [
        f for f in all_files if f.lower().split('.')[-1] in extensions
    ]

    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logged = f.read().splitlines()
    else:
        logged = []

    new_files = list(set(filtered) - set(logged))
    return new_files


def update_file_log(log_path, files):
    with open(log_path, "a", encoding="utf-8") as f:
        for file in files:
            f.write(file + "\n")


def get_audio_metadata(file_path):
    try:
        audio = MP3(file_path, ID3=ID3)
        title = audio.tags.get("TIT2")
        artist = audio.tags.get("TPE1")
        return (
            title.text[0] if title else os.path.basename(file_path),
            artist.text[0] if artist else "Unknown Artist"
        )
    except Exception as e:
        print(
            f"❌ Error reading metadata for {os.path.basename(file_path)}: {e}")
        return os.path.basename(file_path), "Unknown Artist"


def generate_caption(artist_name, song_name):
    prompt = f"""
        Analyze '{song_name}' by {artist_name} and provide EITHER:
        A) The 4 most iconic ACTUAL lyrics (if meaningful), OR
        B) A poetic 2-line interpretation (if lyrics are shallow/unavailable).

        Format EXACTLY like this:

        *"Line 1...
        Line 2...
        Line 3...
        Line 4..."* [emoji]

        #genre1 #genre2 🖤
        🎧 — @deadbutterflly

        RULES:
        1. FOR LYRICS:
        - Must be verbatim from the song
        - Only select if lines have clear emotional/philosophical weight
        - Add "..." line endings

        2. FOR POETRY:
        - Create vivid metaphors about the song's:
            • Title symbolism
            • Artist's signature style
            • Emotional atmosphere
        - Use sensory language (e.g., "amber silence", "neon loneliness")

        3. NEVER add notes/explanations
        4. ALWAYS use *"..."* and 1 mood emoji

        EXAMPLE OUTPUTS:
        1) For meaningful lyrics (*"Hurt"* by Johnny Cash):
        *"I hurt myself today...
        To see if I still feel...
        I focus on the pain...
        The only thing that's real..."* 💔

        2) For shallow lyrics (*"Turn Up the Music"* by Chris Brown):
        *"The bass is a heartbeat...
        Lights trace our skin...
        Tonight we're just shadows...
        Dancing in the din..."* 🔥

        #pop #soul 🖤
        🎧 — @deadbutterflly

        Generate for '{song_name}':
        """

    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        generated_caption = completion.choices[0].message.content
        return generated_caption

    except Exception as e:
        print(e)


async def send_file(app, title, artist, file_path, retries=0):
    print(f"📤 Uploading: {os.path.basename(file_path)}")
    caption = generate_caption(artist, title)
    while retries < MAX_RETRIES:
        try:
            with open(file_path, "rb") as audio:
                await app.bot.send_audio(
                    chat_id=CHAT_ID,
                    audio=audio,
                    title=title,
                    performer=artist,
                    caption=caption,
                    read_timeout=TIMEOUT,
                    write_timeout=TIMEOUT,
                    connect_timeout=TIMEOUT,
                )
            print(f"✅ Successfully uploaded: {os.path.basename(file_path)}")
            return True

        except Exception as e:
            print(
                f"❌ Failed to upload {os.path.basename(file_path)} (Attempt {retries + 1}/{MAX_RETRIES}): {str(e)}")
            retries += 1
            await asyncio.sleep(2 ** retries)

    print(
        f"🚫 Giving up on {os.path.basename(file_path)} after {MAX_RETRIES} attempts.")
    return False


# === MAIN SCRIPT ===
async def main():
    print("🎵 Starting music upload process...")
    new_files = get_new_files(MUSIC_DIR, LOG_FILE, SUPPORTED_EXTENSIONS)

    # Use a context manager to handle the bot's lifecycle:
    # context manager : which are Python objects that need to do something before and after a block of code.
    async with Application.builder().token(BOT_TOKEN).build() as app:
        if new_files:
            print(f"📁 Found {len(new_files)} new files to process")
            uploaded_files = []

            for file in new_files:
                file_path = os.path.join(MUSIC_DIR, file)
                title, artist = get_audio_metadata(file_path)
                success = await send_file(app, title, artist, file_path)
                if success:
                    uploaded_files.append(file)
                else:
                    print(
                        f"⚠️ Skipping {file} due to repeated upload failure.")

            if uploaded_files:
                update_file_log(LOG_FILE, uploaded_files)
                print(
                    f"✅ Upload complete: {len(uploaded_files)} files uploaded successfully")
            else:
                print("❌ No files were successfully uploaded")
        else:
            print("📂 No new music files found in the folder")


if __name__ == "__main__":
    asyncio.run(main())
