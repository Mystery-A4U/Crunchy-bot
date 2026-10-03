import os
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Optional: restrict administrative upload commands to your Telegram user ID.
ADMIN_ID = int(os.environ["ADMIN_ID"]) if os.getenv("ADMIN_ID") else None
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

app = Client(
    "mtproto_uploader",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

def is_admin(message: Message) -> bool:
    return ADMIN_ID is None or (message.from_user and message.from_user.id == ADMIN_ID)

@app.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_text(
        "MTProto uploader is online.\n\n"
        "Send me a media/document and I can re-upload it to TARGET_CHAT_ID "
        "when configured."
    )

@app.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def reupload(_, message: Message):
    if not is_admin(message):
        await message.reply_text("Not authorized.")
        return

    if not TARGET_CHAT_ID:
        await message.reply_text("TARGET_CHAT_ID is not configured.")
        return

    status = await message.reply_text("Downloading media temporarily...")
    temp_dir = Path("/tmp/mtproto_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        path = await message.download(file_name=str(temp_dir) + "/")
        await status.edit_text("Uploading to target chat...")
        await app.send_document(
            TARGET_CHAT_ID,
            document=path,
            caption=message.caption or None,
        )
        await status.edit_text("Uploaded successfully.")
    except Exception as exc:
        await status.edit_text(f"Upload failed: {type(exc).__name__}: {exc}")
    finally:
        if "path" in locals() and path:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass

@app.on_message(filters.command("upload") & filters.private)
async def upload_path(_, message: Message):
    if not is_admin(message):
        await message.reply_text("Not authorized.")
        return

    if not TARGET_CHAT_ID:
        await message.reply_text("TARGET_CHAT_ID is not configured.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.reply_text("Usage: /upload /path/to/file")
        return

    path = Path(parts[1]).expanduser()
    if not path.is_file():
        await message.reply_text("File not found.")
        return

    status = await message.reply_text("Uploading...")
    try:
        await app.send_document(TARGET_CHAT_ID, document=str(path))
        await status.edit_text("Uploaded successfully.")
    except Exception as exc:
        await status.edit_text(f"Upload failed: {type(exc).__name__}: {exc}")

print("MTProto uploader starting...")
app.run()
