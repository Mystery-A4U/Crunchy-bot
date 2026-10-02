"""
tg.py — CrunchyBot Telegram interface
Clean UI with quoted texts, premium account system, Railway-ready.
"""
import re
import os
import traceback
from functools import wraps
from contextlib import suppress
import time
import math
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import subprocess
from platform_tools import display_command, resolve_executable, run_command, split_command

from crunchyroll import (
    Crunchyroll, CrunchyrollAuth, CrunchyrollLicense,
    parse_mpd_content, get_segment_link_list, download_segment,
    get_filter_complex, convert_vtt_to_srt_custom,
    get_episode_display_number, get_episode_title,
    parse_episode_selection, get_download_path,
    get_encrypted_media_path, get_temp_path,
    resolve_encoding_config, EncodingConfig,
)
from config import *

from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
)
from pyrogram.errors import MessageNotModified, QueryIdInvalid

# ─────────────────────────────────────────────────────────────
#  UI STRINGS  (edit these to change all bot messages at once)
# ─────────────────────────────────────────────────────────────
UI = {
    # Welcome
    "start": (
        "🎌  *Welcome to CrunchyBot*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "「 Your personal Crunchyroll downloader — fast, clean, and ad-free. 」\n\n"
        "📌  *How to use:*\n"
        "  • `/dl <url>` — download an episode or series\n"
        "  • `/dl <title>` — search by name\n"
        "  • `/help` — full command list\n\n"
        "⚡  *Your tier:* {tier}"
    ),
    "help": (
        "📖  *CrunchyBot — Help*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "「 Every great journey begins with a single command. 」\n\n"
        "**Commands**\n"
        "`/start` — welcome screen\n"
        "`/help` — this message\n"
        "`/dl <url or title>` — start a download\n"
        "`/cancel` — cancel active session\n"
        "`/mystatus` — check your account tier\n\n"
        "**Download Tiers**\n"
        "┌ 👤 Regular — 480p max · 2 audio tracks\n"
        "├ ⭐ Premium — 1080p max · unlimited audio\n"
        "└ 🔑 Sudo    — no limits · admin commands\n\n"
        "**Admin Commands** _(sudo only)_\n"
        "`/addpremium <id>` · `/rempremium <id>` · `/listpremium`\n"
        "`/addsudo <id>` · `/remsudo <id>` · `/listsudo`\n\n"
        "「 Powered by Crunchyroll API · Built for speed. 」"
    ),
    "cancel_ok": "「 Session cancelled. Start fresh with /dl anytime. 」",
    "cancel_none": "「 Nothing to cancel — no active session found. 」",
    "no_permission": "🚫  「 You don't have permission for this action. 」",
    "active_download": "⏳  「 Please wait — your previous download is still in progress. 」",
    "no_url": (
        "⚠️  Please provide a URL or title.\n\n"
        "  `/dl one piece`\n"
        "  `/dl https://www.crunchyroll.com/watch/...`"
    ),
    "processing": "⚙️  「 Fetching content info from Crunchyroll... 」",
    "searching": "🔍  「 Searching Crunchyroll for *{query}*... 」",
    "no_results": "❌  「 No results found for that title. Try a different search. 」",
    "select_result": "🔎  *Search Results*\n\n「 Select the title you want to download: 」",
    "fetch_video": "📡  「 Fetching video stream information... 」",
    "no_video": "❌  「 Video not accessible: {reason} 」",
    "no_mpd": "❌  「 Could not retrieve stream manifest. 」",
    "no_streams": "❌  「 No video streams found in manifest. 」",
    "fetch_series": "📡  「 Fetching series information... 」",
    "series_not_found": "❌  「 Series not found or no episodes available. 」",
    "series_found": (
        "📺  *{title}*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "「 {count} episode(s) available 」\n\n"
        "{preview}\n\n"
        "**Select episodes to download:**\n"
        "`10` · `1,2,3,5` · `1-10` · `all`"
    ),
    "select_quality": "🎬  「 Choose your video quality: 」",
    "no_quality": "❌  「 No video qualities available within your tier limits. 」",
    "select_audio": (
        "🔊  「 Choose audio language(s) — max {limit}: 」\n\n"
        "Press *Done* when finished."
    ),
    "select_subs": "📝  「 Choose subtitle/caption tracks: 」\n\nPress *Done* when finished.",
    "no_subs": "「 No subtitles available. Proceeding to download... 」",
    "confirm": (
        "✅  *Ready to Download*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{summary}\n"
        "「 Confirm to start — this may take a few minutes. 」"
    ),
    "starting": "🚀  「 Starting download pipeline... 」",
    "uploading": "📤  「 Upload in progress... 」",
    "upload_done": "✅  「 Done! `{name}` has been delivered. 」",
    "download_failed": "❌  「 Download failed during processing. 」",
    "error": "⚠️  「 An error occurred: `{error}` 」",
    "batch_start": "📦  「 Starting batch download: *{title}* · {count} episode(s) 」",
    "batch_done": "🎉  「 Batch complete: *{title}* · {done}/{total} episode(s) downloaded. 」",
    "batch_none": "⚠️  「 No episodes were successfully processed. 」",
    "ep_skip": "⏭  「 {ep} — {reason}. Skipping. 」",
    "session_expired": "⚠️  「 Session expired. Please start again with /dl. 」",
    "invalid_ep": "⚠️  「 Invalid input. Use: `10`, `1,2,3`, `1-10`, or `all` (max {total}). 」",
    "login_failed": (
        "❌  *Crunchyroll Login Failed*\n\n"
        "「 `{error}` 」\n\n"
        "Premium videos require a valid account. "
        "Set `CR_USE_ACCOUNT=false` for free/guest mode."
    ),
    "auth_failed": "❌  「 Crunchyroll authentication failed. 」",
    # Admin responses
    "added_premium": "⭐  「 User `{uid}` added to Premium. 」",
    "already_premium": "「 User is already Premium. 」",
    "removed_premium": "「 User `{uid}` removed from Premium. 」",
    "not_premium": "「 User is not in the Premium list. 」",
    "list_premium_empty": "「 No premium users yet. 」",
    "list_premium": "⭐  *Premium Users*\n\n{list}",
    "added_sudo": "🔑  「 User `{uid}` added to Sudo. 」",
    "already_sudo": "「 User is already Sudo. 」",
    "removed_sudo": "「 User `{uid}` removed from Sudo. 」",
    "cant_remove_self": "「 You cannot remove yourself from Sudo. 」",
    "not_sudo": "「 User is not in the Sudo list. 」",
    "list_sudo_empty": "「 No sudo users — this shouldn't happen! 」",
    "list_sudo": "🔑  *Sudo Users*\n\n{list}",
    "usage_addpremium": "「 Usage: `/addpremium <user_id>` 」",
    "usage_rempremium": "「 Usage: `/rempremium <user_id>` 」",
    "usage_addsudo": "「 Usage: `/addsudo <user_id>` 」",
    "usage_remsudo": "「 Usage: `/remsudo <user_id>` 」",
    # Status
    "status": (
        "👤  *Your Account*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "「 User ID: `{uid}` 」\n"
        "「 Tier: *{tier}* 」\n"
        "「 Max Quality: *{quality}* 」\n"
        "「 Max Audio Tracks: *{audio}* 」"
    ),
}

TIER_LABEL = {
    "sudo":    "🔑 Sudo (Unlimited)",
    "premium": "⭐ Premium",
    "regular": "👤 Regular",
}

# ─────────────────────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────────────────────
try:
    auth = CrunchyrollAuth()
    encoding_config = resolve_encoding_config()
    print(f"[CrunchyBot] Encoding: {encoding_config.summary()}")
except Exception as e:
    print(f"[CrunchyBot] Init error: {e}")
    raise SystemExit(1)

app = Client(
    "crunchyroll_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────
def get_user_tier(user_id: int) -> str:
    if user_id in sudo_users:
        return "sudo"
    if user_id in premium_users:
        return "premium"
    return "regular"


def get_user_limits(user_id: int):
    """Returns (max_audio_tracks, max_video_height_p)."""
    tier = get_user_tier(user_id)
    if tier in ("sudo", "premium"):
        return float("inf"), float("inf")
    return REGULAR_USER_AUDIO_LIMIT, REGULAR_USER_VIDEO_LIMIT_P


def check_user_tier(tier="regular"):
    def decorator(func):
        @wraps(func)
        def wrapper(client, update):
            uid = update.from_user.id
            allowed = False
            if tier == "sudo" and uid in sudo_users:
                allowed = True
            elif tier == "premium" and (uid in sudo_users or uid in premium_users):
                allowed = True
            elif tier == "regular":
                allowed = True
            if allowed:
                return func(client, update)
            if isinstance(update, CallbackQuery):
                update.answer(UI["no_permission"], show_alert=True)
            elif isinstance(update, Message):
                update.reply_text(UI["no_permission"])
        return wrapper
    return decorator


def check_active_download(func):
    @wraps(func)
    def wrapper(client, update):
        uid = update.from_user.id
        if isinstance(update, CallbackQuery) and update.data == "cancel":
            return func(client, update)
        if uid in sudo_users:
            return func(client, update)
        if active_downloads.get(uid):
            if isinstance(update, CallbackQuery):
                update.answer(UI["active_download"], show_alert=True)
            elif isinstance(update, Message):
                update.reply_text(UI["active_download"])
            return
        return func(client, update)
    return wrapper


def edit_message(message: Message, text: str, keyboard: InlineKeyboardMarkup = None):
    with suppress(MessageNotModified, QueryIdInvalid):
        message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.MARKDOWN)


def run_shell_command(command):
    if isinstance(command, str):
        command = split_command(command)
    result = run_command(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout, result.stderr, result.returncode


def get_decryption_key(license_response):
    if not license_response or "key" not in license_response:
        return None
    keys = license_response.get("key") or []
    for key in keys:
        if str(key.get("type", "")).upper() == "CONTENT":
            return "{}:{}".format(key["kid_hex"], key["key_hex"])
    for key in keys:
        if key.get("kid_hex") and key.get("key_hex"):
            return "{}:{}".format(key["kid_hex"], key["key_hex"])
    return None


def get_download_access_filter():
    if AUTHORIZED_USERS:
        f = filters.chat(AUTHORIZED_USERS)
    else:
        f = filters.private
    if sudo_users:
        f = f | filters.user(sudo_users)
    return f


DOWNLOAD_ACCESS_FILTER = get_download_access_filter()


# ─────────────────────────────────────────────────────────────
#  UPLOAD HELPERS
# ─────────────────────────────────────────────────────────────
def humanbytes(size):
    if not size:
        return "0 B"
    power = 2 ** 10
    n = 0
    labels = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size >= power and n < len(labels) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {labels[n]}"


def get_readable_time(seconds: int) -> str:
    result = ""
    days, rem = divmod(int(seconds), 86400)
    if days: result += f"{days}d "
    hours, rem = divmod(rem, 3600)
    if hours: result += f"{hours}h "
    minutes, secs = divmod(rem, 60)
    if minutes: result += f"{minutes}m "
    result += f"{int(secs)}s"
    return result.strip()


def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = max(now - start, 0.001)
    if total <= 0:
        return
    if round(diff % 10.00) == 0 or current == total:
        pct = current * 100 / total
        speed = current / diff
        eta = get_readable_time(round((total - current) / speed)) if speed else "0s"
        filled = math.floor(pct / 5)
        bar = "█" * filled + "░" * (20 - filled)
        text = (
            f"`[{bar}]` `{pct:.1f}%`\n"
            f"`{humanbytes(current)}` / `{humanbytes(total)}`\n"
            f"⚡ Speed: `{humanbytes(speed)}/s`\n"
            f"⏱ ETA: `{eta}`"
        )
        try:
            message.edit(f"{ud_type}\n\n{text}")
        except Exception:
            pass


def get_duration(filepath):
    try:
        parser = createParser(filepath)
        if not parser:
            return 0
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            return metadata.get("duration").seconds
    except Exception as e:
        print(f"Duration error: {e}")
    return 0


def get_thumbnail(in_filename, ttl):
    out = f"/tmp/thumb_{int(time.time())}.jpg"
    try:
        r = subprocess.run(
            ["ffmpeg", "-ss", str(ttl), "-i", in_filename, "-frames:v", "1", "-q:v", "2", "-y", out],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return out if r.returncode == 0 else None
    except Exception:
        return None


class TGUploader:
    def __init__(self, app, msg):
        self.app = app
        self.msg = msg

    def upload_file(self, file_path):
        thumb = None
        try:
            name = os.path.basename(file_path)
            duration = get_duration(file_path)
            thumb = get_thumbnail(file_path, duration / 2)
            caption = f"`{name}`"
            send_kwargs = dict(
                video=file_path,
                chat_id=self.msg.chat.id,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=(UI["uploading"], self.msg, time.time()),
                duration=duration,
                width=1280,
                height=720,
            )
            if thumb:
                send_kwargs["thumb"] = thumb
            self.app.send_video(**send_kwargs)
        except Exception as e:
            print(e)
            self.msg.edit(UI["error"].format(error=e))
        finally:
            if thumb:
                with suppress(Exception):
                    os.remove(thumb)


# ─────────────────────────────────────────────────────────────
#  COMMANDS
# ─────────────────────────────────────────────────────────────
@app.on_message(filters.command("start"))
def cmd_start(client, message: Message):
    uid = message.from_user.id
    tier = TIER_LABEL[get_user_tier(uid)]
    message.reply_text(
        UI["start"].format(tier=tier),
        parse_mode=enums.ParseMode.MARKDOWN,
    )


@app.on_message(filters.command("help"))
def cmd_help(client, message: Message):
    message.reply_text(UI["help"], parse_mode=enums.ParseMode.MARKDOWN)


@app.on_message(filters.command("mystatus"))
def cmd_mystatus(client, message: Message):
    uid = message.from_user.id
    tier = get_user_tier(uid)
    max_audio, max_q = get_user_limits(uid)
    message.reply_text(
        UI["status"].format(
            uid=uid,
            tier=TIER_LABEL[tier],
            quality="Unlimited" if max_q == float("inf") else f"{max_q}p",
            audio="Unlimited" if max_audio == float("inf") else str(max_audio),
        ),
        parse_mode=enums.ParseMode.MARKDOWN,
    )


@app.on_message(filters.command("cancel"))
def cmd_cancel(client, message: Message):
    uid = message.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        if state.get("message"):
            edit_message(state["message"], UI["cancel_ok"])
        else:
            message.reply_text(UI["cancel_ok"])
        active_downloads.pop(uid, None)
    else:
        message.reply_text(UI["cancel_none"])


# ── Premium management ───────────────────────────────────────
@app.on_message(filters.command("addpremium") & filters.user(sudo_users))
def cmd_add_premium(client, message: Message):
    try:
        uid = int(message.text.split(maxsplit=1)[1])
        if uid not in premium_users:
            premium_users.append(uid)
            message.reply_text(UI["added_premium"].format(uid=uid), parse_mode=enums.ParseMode.MARKDOWN)
        else:
            message.reply_text(UI["already_premium"])
    except (IndexError, ValueError):
        message.reply_text(UI["usage_addpremium"], parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        message.reply_text(UI["error"].format(error=e))


@app.on_message(filters.command("rempremium") & filters.user(sudo_users))
def cmd_rem_premium(client, message: Message):
    try:
        uid = int(message.text.split(maxsplit=1)[1])
        if uid in premium_users:
            premium_users.remove(uid)
            message.reply_text(UI["removed_premium"].format(uid=uid), parse_mode=enums.ParseMode.MARKDOWN)
        else:
            message.reply_text(UI["not_premium"])
    except (IndexError, ValueError):
        message.reply_text(UI["usage_rempremium"], parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        message.reply_text(UI["error"].format(error=e))


@app.on_message(filters.command("listpremium") & filters.user(sudo_users))
def cmd_list_premium(client, message: Message):
    if not premium_users:
        message.reply_text(UI["list_premium_empty"])
    else:
        lst = "\n".join(f"⭐ `{uid}`" for uid in premium_users)
        message.reply_text(UI["list_premium"].format(list=lst), parse_mode=enums.ParseMode.MARKDOWN)


# ── Sudo management ──────────────────────────────────────────
@app.on_message(filters.command("addsudo") & filters.user(sudo_users))
def cmd_add_sudo(client, message: Message):
    try:
        uid = int(message.text.split(maxsplit=1)[1])
        if uid not in sudo_users:
            sudo_users.append(uid)
            message.reply_text(UI["added_sudo"].format(uid=uid), parse_mode=enums.ParseMode.MARKDOWN)
        else:
            message.reply_text(UI["already_sudo"])
    except (IndexError, ValueError):
        message.reply_text(UI["usage_addsudo"], parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        message.reply_text(UI["error"].format(error=e))


@app.on_message(filters.command("remsudo") & filters.user(sudo_users))
def cmd_rem_sudo(client, message: Message):
    try:
        uid = int(message.text.split(maxsplit=1)[1])
        if uid == message.from_user.id:
            message.reply_text(UI["cant_remove_self"])
            return
        if uid in sudo_users:
            sudo_users.remove(uid)
            message.reply_text(UI["removed_sudo"].format(uid=uid), parse_mode=enums.ParseMode.MARKDOWN)
        else:
            message.reply_text(UI["not_sudo"])
    except (IndexError, ValueError):
        message.reply_text(UI["usage_remsudo"], parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        message.reply_text(UI["error"].format(error=e))


@app.on_message(filters.command("listsudo") & filters.user(sudo_users))
def cmd_list_sudo(client, message: Message):
    if not sudo_users:
        message.reply_text(UI["list_sudo_empty"])
    else:
        lst = "\n".join(f"🔑 `{uid}`" for uid in sudo_users)
        message.reply_text(UI["list_sudo"].format(list=lst), parse_mode=enums.ParseMode.MARKDOWN)


# ─────────────────────────────────────────────────────────────
#  DOWNLOAD COMMAND
# ─────────────────────────────────────────────────────────────
@app.on_message(filters.command(["download", "dl"]) & DOWNLOAD_ACCESS_FILTER)
@check_active_download
def cmd_download(client, message: Message):
    global crunchyroll, license_handler, vid_token
    uid = message.from_user.id

    # Authenticate
    if use_account and Email and Password:
        vid_token = auth.get_user_token(Email, Password, allow_guest_fallback=False)
        if not vid_token:
            message.reply_text(
                UI["login_failed"].format(error=auth.last_auth_error or "unknown error"),
                parse_mode=enums.ParseMode.MARKDOWN,
            )
            return
    else:
        vid_token = auth.get_guest_token()
    if not vid_token:
        message.reply_text(UI["auth_failed"])
        return

    crunchyroll = Crunchyroll(
        vid_token,
        playback_endpoint=auth.playback_endpoint,
        playback_user_agent=auth.playback_user_agent,
        auth_instance=auth,
        email=Email if use_account else None,
        password=Password if use_account else None,
    )
    license_handler = CrunchyrollLicense()

    if len(message.command) < 2:
        message.reply_text(UI["no_url"], parse_mode=enums.ParseMode.MARKDOWN)
        return

    video_url = " ".join(message.command[1:]).strip()
    status_msg = message.reply_text(UI["processing"], parse_mode=enums.ParseMode.MARKDOWN)

    user_states[uid] = {
        "step": "initial",
        "url": video_url,
        "data": {},
        "message": status_msg,
        "is_series": False,
    }
    process_download_url(client, uid, video_url, status_msg)


# ─────────────────────────────────────────────────────────────
#  FLOW FUNCTIONS
# ─────────────────────────────────────────────────────────────
def search_button_label(result):
    title = result.get("title", "Untitled")
    if len(title) > 40:
        title = title[:37].rstrip() + "…"
    access = result.get("access", "?")
    kind   = result.get("type", "?")
    icon   = "⭐" if access == "premium" else "🆓"
    return f"{icon} [{kind.upper()}]  {title}"


def show_search_results(client, uid, query, status_msg):
    edit_message(status_msg, UI["searching"].format(query=query), None)
    results = crunchyroll.search(query, limit=5)
    if not results:
        edit_message(status_msg, UI["no_results"])
        user_states.pop(uid, None)
        return

    user_states[uid]["step"] = "select_search"
    user_states[uid]["data"]["search_results"] = results

    buttons = [
        [InlineKeyboardButton(search_button_label(r), callback_data=f"search_{i}")]
        for i, r in enumerate(results)
    ]
    buttons.append([InlineKeyboardButton("✖ Cancel", callback_data="cancel")])
    edit_message(status_msg, UI["select_result"], InlineKeyboardMarkup(buttons))


def process_download_url(client, uid, video_url, status_msg):
    try:
        if "crunchyroll.com" in video_url and "/watch/" in video_url:
            m = re.search(r'"?https?://www\.crunchyroll\.com/(?:watch)/([^/?"\']+)', video_url)
            if not m:
                edit_message(status_msg, UI["error"].format(error="Invalid episode URL format"))
                user_states.pop(uid, None)
                return
            content_id = m.group(1)
            edit_message(status_msg, UI["fetch_video"])
            video_info = crunchyroll.get_video_info(content_id)
            if not video_info:
                reason = crunchyroll.last_playback_error or "video not found"
                edit_message(status_msg, UI["no_video"].format(reason=reason))
                user_states.pop(uid, None)
                return

            pssh, mpd_content, token = crunchyroll.get_pssh(video_info)
            if not mpd_content:
                edit_message(status_msg, UI["no_mpd"])
                user_states.pop(uid, None)
                return

            video_list, _ = parse_mpd_content(mpd_content)
            if not video_list:
                edit_message(status_msg, UI["no_streams"])
                user_states.pop(uid, None)
                return

            user_states[uid]["data"].update({
                "video_info": video_info, "id": content_id,
                "pssh": pssh, "mpd_content": mpd_content, "drm_token": token,
                "available_video_qualities": video_list,
            })
            user_states[uid]["is_series"] = False
            ask_video_quality(client, uid)

        elif "crunchyroll.com" in video_url and "/series/" in video_url:
            edit_message(status_msg, UI["fetch_series"])
            series_data, series_info = crunchyroll.get_content_info(url=video_url)
            if not series_data or not series_data.get("data"):
                edit_message(status_msg, UI["series_not_found"])
                user_states.pop(uid, None)
                return

            episodes = [
                {
                    "episode_no": get_episode_display_number(ep, idx + 1),
                    "guid": ep["id"],
                    "title": get_episode_title(ep, idx + 1),
                }
                for idx, ep in enumerate(series_data["data"])
            ]
            payload = series_info.get("data")
            if isinstance(payload, list) and payload:
                series_title = payload[0].get("title", "Unknown Series")
            elif isinstance(payload, dict):
                series_title = payload.get("title", "Unknown Series")
            else:
                series_title = "Unknown Series"

            preview = "\n".join(
                f"  `{idx}.` E{ep['episode_no']} — {ep['title'][:45]}"
                for idx, ep in enumerate(episodes[:15], 1)
            )
            if len(episodes) > 15:
                preview += f"\n  … and {len(episodes) - 15} more"

            user_states[uid]["data"].update({
                "episodes": episodes,
                "series_title": series_title,
                "total_episodes": len(episodes),
            })
            user_states[uid]["is_series"] = True
            user_states[uid]["step"] = "ask_episode_count"

            edit_message(
                status_msg,
                UI["series_found"].format(title=series_title, count=len(episodes), preview=preview),
                InlineKeyboardMarkup([[InlineKeyboardButton("✖ Cancel", callback_data="cancel")]]),
            )
        else:
            show_search_results(client, uid, video_url, status_msg)

    except Exception as e:
        traceback.print_exc()
        edit_message(status_msg, UI["error"].format(error=e))
        user_states.pop(uid, None)


def ask_video_quality(client, uid):
    if uid not in user_states:
        return
    state = user_states[uid]
    status_msg = state["message"]
    video_list = state["data"]["available_video_qualities"]
    _, max_q = get_user_limits(uid)

    buttons = []
    for i, v in enumerate(video_list):
        h = int(v.get("height", 0))
        if h <= max_q:
            kbps = int(v.get("bandwidth", 0)) // 1000
            icon = "🔵" if h >= 1080 else ("🟢" if h >= 720 else "🟡")
            buttons.append([InlineKeyboardButton(f"{icon}  {h}p  ·  {kbps} kbps", callback_data=f"quality_{i}")])

    if not buttons:
        edit_message(status_msg, UI["no_quality"])
        user_states.pop(uid, None)
        return

    buttons.append([InlineKeyboardButton("✖ Cancel", callback_data="cancel")])
    state["step"] = "select_quality"
    edit_message(status_msg, UI["select_quality"], InlineKeyboardMarkup(buttons))


def ask_audio_language(client, uid):
    if uid not in user_states:
        return
    state = user_states[uid]
    status_msg = state["message"]
    video_info = state["data"]["video_info"]

    if not video_info.get("versions"):
        state["data"]["selected_audios"] = []
        ask_subtitles(client, uid)
        return

    max_a, _ = get_user_limits(uid)
    state["data"]["selected_audios"] = []
    audio_options = {}

    buttons = []
    for v in video_info["versions"]:
        locale = v["audio_locale"]
        guid   = v["guid"]
        name   = locale_map.get(locale, locale)
        audio_options[guid] = locale
        buttons.append([InlineKeyboardButton(f"🔊  {name}", callback_data=f"audio_{guid}")])

    state["data"]["available_audio_options"] = audio_options
    limit_label = "∞" if max_a == float("inf") else str(max_a)
    buttons.append([
        InlineKeyboardButton(f"✔ Done  (0 / {limit_label})", callback_data="audio_done"),
        InlineKeyboardButton("✖ Cancel", callback_data="cancel"),
    ])
    state["step"] = "select_audio"
    edit_message(
        status_msg,
        UI["select_audio"].format(limit=limit_label),
        InlineKeyboardMarkup(buttons),
    )


def ask_subtitles(client, uid):
    if uid not in user_states:
        return
    state = user_states[uid]
    status_msg = state["message"]
    video_info = state["data"]["video_info"]
    track_info_list = []

    def add_track(lang, data, kind):
        if lang == "none" or not data.get("url"):
            return
        prefix = "CC" if kind == "caption" else "SUB"
        lang_display = locale_map.get(lang, lang)
        track_info_list.append({
            "type": kind, "language": lang, "url": data["url"],
            "format": data.get("format", "vtt"), "display_name": lang_display,
            "prefix": prefix,
        })

    for lang, data in (video_info.get("captions") or {}).items():
        add_track(lang, data, "caption")
    for lang, data in (video_info.get("subtitles") or {}).items():
        add_track(lang, data, "subtitle")

    if not track_info_list:
        edit_message(status_msg, UI["no_subs"])
        state["data"]["selected_subtitles"] = []
        state["data"]["available_subtitle_options"] = []
        state["step"] = "confirm_download"
        confirm_download(client, uid)
        return

    state["data"]["selected_subtitles"] = []
    state["data"]["available_subtitle_options"] = track_info_list

    buttons = []
    for i, t in enumerate(track_info_list):
        icon = "💬" if t["prefix"] == "CC" else "📝"
        buttons.append([InlineKeyboardButton(
            f"{icon}  [{t['prefix']}]  {t['display_name']}",
            callback_data=f"sub_{i}",
        )])
    buttons.append([
        InlineKeyboardButton("✔ Done  (0 selected)", callback_data="sub_done"),
        InlineKeyboardButton("✖ Cancel", callback_data="cancel"),
    ])
    state["step"] = "select_subtitles"
    edit_message(status_msg, UI["select_subs"], InlineKeyboardMarkup(buttons))


def confirm_download(client, uid):
    if uid not in user_states:
        return
    state = user_states[uid]
    status_msg = state["message"]

    sel_q    = state["data"]["selected_video_quality"]
    sel_a    = state["data"]["selected_audios"]
    sel_s    = state["data"]["selected_subtitles"]

    lines = []
    if state["is_series"]:
        lines += [
            f"📺  Series:   *{state['data']['series_title']}*",
            f"🎞  Episodes: *{state['data']['episodes_to_download_count']}*",
        ]
    else:
        cid = state["data"]["id"]
        ep_info  = crunchyroll.get_single_info(cid)["data"][0]
        ep_meta  = ep_info["episode_metadata"]
        anime    = re.sub(r"\s*\([^)]*\)", "", ep_meta["season_title"])
        s_num    = str(ep_meta["season_number"]).zfill(2)
        e_num    = str(ep_meta["episode_number"]).zfill(2)
        lines += [
            f"📺  Anime:    *{anime}*",
            f"🎞  Episode:  *S{s_num}E{e_num}* — {ep_info['title']}",
        ]

    lines += [
        f"🎬  Quality:  *{sel_q['height']}p*",
        f"🔊  Audio:    *{', '.join(a['audio_locale'] for a in sel_a) if sel_a else 'None'}*",
        f"📝  Subs:     *{', '.join(s['language'] for s in sel_s) if sel_s else 'None'}*",
    ]

    summary = "\n".join(f"  {l}" for l in lines)
    buttons = [
        [InlineKeyboardButton("🚀  Start Download", callback_data="confirm_start")],
        [InlineKeyboardButton("✖ Cancel",           callback_data="cancel")],
    ]
    state["step"] = "confirm_download"
    edit_message(status_msg, UI["confirm"].format(summary=summary), InlineKeyboardMarkup(buttons))


# ─────────────────────────────────────────────────────────────
#  TEXT HANDLER (episode selection)
# ─────────────────────────────────────────────────────────────
@app.on_message(filters.text & ~filters.command([
    "start", "help", "mystatus", "download", "dl", "cancel",
    "addpremium", "rempremium", "listpremium",
    "addsudo", "remsudo", "listsudo",
]) & filters.private)
def handle_text_reply(client, message: Message):
    uid = message.from_user.id
    if uid not in user_states or user_states[uid]["step"] != "ask_episode_count":
        return

    state      = user_states[uid]
    status_msg = state["message"]

    try:
        total = state["data"]["total_episodes"]
        indices = parse_episode_selection(message.text.strip(), total)
        state["data"]["episodes"] = [state["data"]["episodes"][i] for i in indices]
        state["data"]["episodes_to_download_count"] = len(state["data"]["episodes"])

        edit_message(status_msg, "📡  「 Fetching stream info for selected episodes... 」")

        video_info = mpd_content = None
        for ep in state["data"]["episodes"]:
            video_info = crunchyroll.get_video_info(ep["guid"])
            if not video_info:
                continue
            _, mpd_content, _ = crunchyroll.get_pssh(video_info)
            if mpd_content:
                break

        if not video_info or not mpd_content:
            edit_message(status_msg, "❌  「 Selected episodes not accessible. Premium account may be required. 」")
            user_states.pop(uid, None)
            return

        video_list, _ = parse_mpd_content(mpd_content)
        if not video_list:
            edit_message(status_msg, UI["no_streams"])
            user_states.pop(uid, None)
            return

        state["data"]["video_info"] = video_info
        state["data"]["available_video_qualities"] = video_list
        ask_video_quality(client, uid)

    except ValueError:
        message.reply_text(
            UI["invalid_ep"].format(total=state["data"]["total_episodes"]),
            parse_mode=enums.ParseMode.MARKDOWN,
        )
    except Exception as e:
        traceback.print_exc()
        edit_message(status_msg, UI["error"].format(error=e))
        user_states.pop(uid, None)


# ─────────────────────────────────────────────────────────────
#  CALLBACK HANDLER
# ─────────────────────────────────────────────────────────────
@app.on_callback_query()
@check_active_download
def handle_callback(client, query: CallbackQuery):
    uid  = query.from_user.id
    data = query.data

    if uid not in user_states:
        query.answer(UI["session_expired"], show_alert=True)
        with suppress(Exception):
            query.message.delete()
        return

    state      = user_states[uid]
    status_msg = state["message"]
    step       = state["step"]

    try:
        # ── Cancel ──────────────────────────────────────────
        if data == "cancel":
            query.answer("Cancelled")
            edit_message(status_msg, UI["cancel_ok"])
            user_states.pop(uid, None)
            active_downloads.pop(uid, None)
            return

        # ── Search result ────────────────────────────────────
        if step == "select_search" and data.startswith("search_"):
            idx = int(data.split("_")[1])
            results = state["data"].get("search_results", [])
            if idx < 0 or idx >= len(results):
                query.answer("Invalid selection", show_alert=True)
                return
            sel = results[idx]
            query.answer(sel["title"][:50])
            state["url"]      = sel["url"]
            state["data"]     = {}
            state["is_series"] = False
            state["step"]     = "initial"
            edit_message(status_msg, f"「 Selected: *{sel['title']}* — fetching... 」")
            process_download_url(client, uid, sel["url"], status_msg)
            return

        # ── Quality ──────────────────────────────────────────
        if step == "select_quality" and data.startswith("quality_"):
            qi = int(data.split("_")[1])
            sel_q = state["data"]["available_video_qualities"][qi]
            state["data"]["selected_video_quality"] = sel_q
            query.answer(f"Quality: {sel_q['height']}p")
            ask_audio_language(client, uid)
            return

        # ── Audio ────────────────────────────────────────────
        if step == "select_audio":
            max_a, _ = get_user_limits(uid)
            limit_label = "∞" if max_a == float("inf") else str(max_a)

            if data == "audio_done":
                query.answer("Audio selection confirmed.")
                ask_subtitles(client, uid)
                return

            if data.startswith("audio_"):
                guid = data[6:]
                raw_locale = state["data"]["available_audio_options"].get(guid, guid)
                lang_name  = locale_map.get(raw_locale, raw_locale)
                selected   = state["data"]["selected_audios"]
                existing   = next((i for i, a in enumerate(selected) if a["guid"] == guid), None)

                if existing is not None:
                    selected.pop(existing)
                    query.answer(f"Removed: {lang_name}")
                else:
                    if len(selected) < max_a:
                        selected.append({"audio_locale": lang_name, "guid": guid})
                        query.answer(f"Added: {lang_name}")
                    else:
                        query.answer(f"Max {limit_label} audio tracks reached.", show_alert=True)
                        return

                sel_guids = {a["guid"] for a in selected}
                buttons = []
                for g, loc in state["data"]["available_audio_options"].items():
                    name = locale_map.get(loc, loc)
                    prefix = "✅  " if g in sel_guids else "🔊  "
                    buttons.append([InlineKeyboardButton(f"{prefix}{name}", callback_data=f"audio_{g}")])
                buttons.append([
                    InlineKeyboardButton(f"✔ Done  ({len(selected)} / {limit_label})", callback_data="audio_done"),
                    InlineKeyboardButton("✖ Cancel", callback_data="cancel"),
                ])
                query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
            return

        # ── Subtitles ────────────────────────────────────────
        if step == "select_subtitles":
            if data == "sub_done":
                query.answer("Subtitle selection confirmed.")
                confirm_download(client, uid)
                return

            if data.startswith("sub_"):
                si = int(data[4:])
                track = state["data"]["available_subtitle_options"][si]
                selected = state["data"]["selected_subtitles"]
                existing = next((i for i, s in enumerate(selected) if s["url"] == track["url"]), None)

                if existing is not None:
                    selected.pop(existing)
                    query.answer(f"Removed: {track['display_name']}")
                else:
                    selected.append({
                        "language": track["display_name"],
                        "url": track["url"],
                        "format": track["format"],
                        "type": track["type"],
                        "original_locale": track["language"],
                    })
                    query.answer(f"Added: {track['display_name']}")

                sel_urls = {s["url"] for s in selected}
                buttons = []
                for i, t in enumerate(state["data"]["available_subtitle_options"]):
                    icon = "✅  " if t["url"] in sel_urls else ("💬  " if t["prefix"] == "CC" else "📝  ")
                    buttons.append([InlineKeyboardButton(
                        f"{icon}[{t['prefix']}]  {t['display_name']}",
                        callback_data=f"sub_{i}",
                    )])
                buttons.append([
                    InlineKeyboardButton(f"✔ Done  ({len(selected)} selected)", callback_data="sub_done"),
                    InlineKeyboardButton("✖ Cancel", callback_data="cancel"),
                ])
                query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
            return

        # ── Confirm ──────────────────────────────────────────
        if step == "confirm_download" and data == "confirm_start":
            query.answer("Starting…")
            state["step"] = "downloading"
            active_downloads[uid] = True
            process_download(client, uid)
            return

    except MessageNotModified:
        query.answer()
    except QueryIdInvalid:
        query.answer("Button expired.", show_alert=True)
    except Exception as e:
        traceback.print_exc()
        query.answer("An error occurred.", show_alert=True)
        user_states.pop(uid, None)
        active_downloads.pop(uid, None)
        with suppress(Exception):
            status_msg.edit_text(UI["error"].format(error=e))


# ─────────────────────────────────────────────────────────────
#  DOWNLOAD PIPELINE
# ─────────────────────────────────────────────────────────────
def process_download(client, uid):
    state = user_states.get(uid)
    if not state or state["step"] != "downloading":
        active_downloads.pop(uid, None)
        return

    status_msg = state["message"]
    is_series  = state["is_series"]
    temp_files = []

    try:
        if is_series:
            episodes        = state["data"]["episodes"]
            raw_title       = state["data"]["series_title"]
            series_title    = re.sub(r'[<>:"\'/\\|?*]', "", raw_title)
            output_dir      = series_title
            os.makedirs(output_dir, exist_ok=True)
            total           = len(episodes)
            done            = 0

            edit_message(status_msg, UI["batch_start"].format(title=series_title, count=total))

            for i, ep_info in enumerate(episodes):
                ep_label = f"Episode {i + 1}/{total}"
                ep_id    = ep_info["guid"]

                video_info = crunchyroll.get_video_info(ep_id)
                if not video_info:
                    reason = crunchyroll.last_playback_error or "not accessible"
                    edit_message(status_msg, UI["ep_skip"].format(ep=ep_label, reason=reason))
                    continue

                pssh, mpd_content, token = crunchyroll.get_pssh(video_info)
                if not mpd_content:
                    edit_message(status_msg, UI["ep_skip"].format(ep=ep_label, reason="no MPD"))
                    continue

                video_key = get_decryption_key(license_handler.get_license(pssh, token, ep_id, crunchyroll.token))
                if not video_key:
                    edit_message(status_msg, UI["ep_skip"].format(ep=ep_label, reason="no license key"))
                    continue

                sel_q = state["data"]["selected_video_quality"]
                ep_vlist, _ = parse_mpd_content(mpd_content)
                sel_q = next((v for v in ep_vlist if v["height"] == sel_q["height"]), None)
                if not sel_q:
                    edit_message(status_msg, UI["ep_skip"].format(ep=ep_label, reason="quality not available"))
                    continue

                vidseg = get_segment_link_list(mpd_content, sel_q["name"], sel_q["base_url"])
                if not vidseg or "all" not in vidseg:
                    edit_message(status_msg, UI["ep_skip"].format(ep=ep_label, reason="no video segments"))
                    continue

                # Audio
                ep_audios = _resolve_episode_audios(state, video_info, ep_id)

                # Subtitles
                ep_subs = _resolve_episode_subs(state, video_info, ep_id)

                # Build title
                ep_meta  = crunchyroll.get_single_info(ep_id)["data"][0]["episode_metadata"]
                s_num    = str(ep_meta["season_number"]).zfill(2)
                e_num    = str(ep_meta.get("episode_number", i + 1)).zfill(2)
                ep_title = crunchyroll.get_single_info(ep_id)["data"][0]["title"]
                title    = _build_title(series_title, s_num, e_num, ep_title)

                ep_temp = []
                out = download_decrypt_merge_single(
                    client, uid, status_msg, title, vidseg, video_key,
                    ep_audios, ep_subs, sel_q, ep_temp,
                    output_directory=output_dir,
                    progress_prefix=f"[{ep_label}]  ",
                )
                temp_files += ep_temp

                if out:
                    done += 1
                    edit_message(status_msg, UI["uploading"])
                    TGUploader(app, status_msg).upload_file(out)
                else:
                    edit_message(status_msg, UI["ep_skip"].format(ep=ep_label, reason="processing failed"))

                cleanup_files(ep_temp)

            if done:
                edit_message(status_msg, UI["batch_done"].format(title=series_title, done=done, total=total))
            else:
                edit_message(status_msg, UI["batch_none"])

        else:
            # Single episode
            video_info     = state["data"]["video_info"]
            content_id     = state["data"]["id"]
            pssh           = state["data"]["pssh"]
            mpd_content    = state["data"]["mpd_content"]
            token          = state["data"]["drm_token"]
            sel_q          = state["data"]["selected_video_quality"]
            sel_audios     = state["data"]["selected_audios"]
            sel_subs       = state["data"]["selected_subtitles"]

            video_key = get_decryption_key(license_handler.get_license(pssh, token, content_id, crunchyroll.token))
            if not video_key:
                raise Exception("Failed to get video license key.")

            vidseg = get_segment_link_list(mpd_content, sel_q["name"], sel_q["base_url"])
            if not vidseg or "all" not in vidseg:
                raise Exception("Failed to get video segments.")

            edit_message(status_msg, "🔊  「 Fetching audio stream details... 」")
            detailed_audios = _fetch_detailed_audios(sel_audios)

            ep_data  = crunchyroll.get_single_info(content_id)["data"][0]
            ep_meta  = ep_data["episode_metadata"]
            anime    = re.sub(r"\s*\([^)]*\)", "", ep_meta["season_title"])
            s_num    = str(ep_meta["season_number"]).zfill(2)
            e_num    = str(ep_meta.get("episode_number", 0)).zfill(2)
            ep_title = ep_data["title"]
            title    = _build_title(anime, s_num, e_num, ep_title)

            out = download_decrypt_merge_single(
                client, uid, status_msg, title, vidseg, video_key,
                detailed_audios, sel_subs, sel_q, temp_files,
            )
            if out:
                edit_message(status_msg, UI["uploading"])
                TGUploader(app, status_msg).upload_file(out)
                edit_message(status_msg, UI["upload_done"].format(name=os.path.basename(out)))
            else:
                edit_message(status_msg, UI["download_failed"])

            cleanup_files(temp_files)

    except Exception as e:
        traceback.print_exc()
        edit_message(status_msg, UI["error"].format(error=e))
        cleanup_files(temp_files if "temp_files" in locals() else [])
    finally:
        user_states.pop(uid, None)
        active_downloads.pop(uid, None)


def _build_title(anime, s_num, e_num, ep_title):
    if use_custom_title:
        try:
            title = custom_title.format(Title=anime, Season=s_num, Episode=e_num, EpTitle=ep_title)
        except Exception:
            title = f"{anime}.S{s_num}E{e_num}-{ep_title}"
    else:
        title = f"{anime}.S{s_num}E{e_num}-{ep_title}"
    return re.sub(r'[<>:"\'/\\|?*]', "", title)


def _fetch_detailed_audios(sel_audios):
    out = []
    for audio in sel_audios:
        guid = audio["guid"]
        info = crunchyroll.get_video_info(guid)
        if not info:
            continue
        a_pssh, a_mpd, a_token = crunchyroll.get_pssh(info)
        if not a_mpd:
            continue
        a_key = get_decryption_key(license_handler.get_license(a_pssh, a_token, guid, crunchyroll.token))
        if not a_key:
            continue
        _, a_list = parse_mpd_content(a_mpd)
        highest = max(a_list, key=lambda x: int(x.get("bandwidth", 0)), default=None)
        if not highest:
            continue
        audseg = get_segment_link_list(a_mpd, highest["name"], highest["base_url"])
        if not audseg or "all" not in audseg:
            continue
        out.append({"audio_locale": audio["audio_locale"], "key": a_key, "segment": audseg})
    return out


def _resolve_episode_audios(state, video_info, ep_id):
    out = []
    for sel in state["data"]["selected_audios"]:
        target = None
        for v in video_info.get("versions", []):
            if locale_map.get(v.get("audio_locale"), v.get("audio_locale")) == sel["audio_locale"]:
                target = v.get("guid")
                break
        if not target:
            continue
        a_info = crunchyroll.get_video_info(target)
        if not a_info:
            continue
        a_pssh, a_mpd, a_token = crunchyroll.get_pssh(a_info)
        if not a_mpd:
            continue
        a_key = get_decryption_key(license_handler.get_license(a_pssh, a_token, target, crunchyroll.token))
        if not a_key:
            continue
        _, a_list = parse_mpd_content(a_mpd)
        highest = max(a_list, key=lambda x: int(x.get("bandwidth", 0)), default=None)
        if not highest:
            continue
        audseg = get_segment_link_list(a_mpd, highest["name"], highest["base_url"])
        if audseg and "all" in audseg:
            out.append({"audio_locale": sel["audio_locale"], "key": a_key, "segment": audseg})
    return out


def _resolve_episode_subs(state, video_info, ep_id):
    available = {}
    for lang, data in (video_info.get("subtitles") or {}).items():
        if data.get("url"):
            available[lang] = data
    for lang, data in (video_info.get("captions") or {}).items():
        if data.get("url"):
            available[f"{lang}_caption"] = data

    out = []
    for sel in state["data"]["selected_subtitles"]:
        orig   = sel.get("original_locale")
        kind   = sel.get("type")
        key    = f"{orig}_caption" if kind == "caption" else orig
        found  = available.get(key) or available.get(orig)
        if found and found.get("url"):
            out.append({
                "language": sel["language"], "url": found["url"],
                "format": found.get("format", "vtt"), "type": kind,
            })
    return out


def download_decrypt_merge_single(
    client, uid, status_msg, title, vidseg, video_key,
    detailed_audios, selected_subtitles, video_quality_info, temp_files,
    output_directory="", progress_prefix="",
):
    final_dir = get_download_path(output_directory) if output_directory else get_download_path()
    os.makedirs(final_dir, exist_ok=True)
    temp_dir  = get_temp_path(output_directory or "_single", title)
    os.makedirs(temp_dir, exist_ok=True)

    base_path     = os.path.join(final_dir, title)
    dec_video     = os.path.join(temp_dir, f"{title}.mp4")
    audio_files   = []
    subtitle_files = []

    temp_files += [temp_dir, get_temp_path(f"enc_{title}")]
    headers = {"User-Agent": auth.playback_user_agent}

    try:
        # Video download
        edit_message(status_msg, f"{progress_prefix}⬇  「 Downloading video... 」\n`{dec_video}`")
        download_segment(vidseg["all"], f"enc_{title}", "mp4", headers=headers)

        # Audio downloads
        for i, audio in enumerate(detailed_audios):
            locale = audio["audio_locale"]
            edit_message(status_msg, f"{progress_prefix}🔊  「 Downloading audio {i + 1}/{len(detailed_audios)}: {locale} 」")
            enc_audio_base = f"enc_{title}_{locale}"
            download_segment(audio["segment"]["all"], enc_audio_base, "m4a", headers=headers)
            temp_files.append(get_temp_path(enc_audio_base))

        # Subtitle downloads
        if selected_subtitles:
            edit_message(status_msg, f"{progress_prefix}📝  「 Downloading subtitles... 」")
            for sub in selected_subtitles:
                s_lang   = sub["language"]
                s_fmt    = sub["format"]
                s_url    = sub["url"]
                s_temp   = os.path.join(temp_dir, f"{title}_{s_lang}.{s_fmt}")
                s_final  = os.path.join(temp_dir, f"{title}_{s_lang}.srt")
                _, _, rc = run_shell_command([
                    resolve_executable("curl", project_fallback=False),
                    "-fsSL", "-o", s_temp, s_url,
                ])
                if rc != 0:
                    continue
                temp_files.append(s_temp)
                if s_fmt.lower() == "vtt":
                    try:
                        convert_vtt_to_srt_custom(s_temp, s_final)
                        subtitle_files.append({"path": s_final, "lang": s_lang, "title_lang": s_lang, "type": ".srt"})
                        temp_files.append(s_final)
                    except Exception as ex:
                        print(f"VTT→SRT failed ({s_lang}): {ex}")
                else:
                    subtitle_files.append({"path": s_temp, "lang": s_lang, "title_lang": s_lang, "type": sub["type"]})

        # Decrypt video
        edit_message(status_msg, f"{progress_prefix}🔓  「 Decrypting video... 」")
        enc_v = get_encrypted_media_path(f"enc_{title}", "mp4")
        _, stderr, rc = run_shell_command([resolve_executable("mp4decrypt"), enc_v, dec_video, "--show-progress", "--key", video_key])
        if rc != 0:
            raise Exception(f"Video decryption failed: {stderr}")

        # Decrypt audio
        for i, audio in enumerate(detailed_audios):
            locale  = audio["audio_locale"]
            edit_message(status_msg, f"{progress_prefix}🔓  「 Decrypting audio {i + 1}/{len(detailed_audios)}: {locale} 」")
            enc_a   = get_encrypted_media_path(f"enc_{title}_{locale}", "m4a")
            dec_a   = os.path.join(temp_dir, f"{title}_{locale}.m4a")
            _, se, rc = run_shell_command([resolve_executable("mp4decrypt"), enc_a, dec_a, "--show-progress", "--key", audio["key"]])
            if rc != 0:
                print(f"Audio decryption failed ({locale}): {se}")
                continue
            audio_files.append({"path": dec_a, "lang": locale_map.get(locale), "title_lang": locale})
            temp_files.append(dec_a)

        # Merge
        edit_message(status_msg, f"{progress_prefix}⚙  「 Merging streams... 」")
        enc_cfg = resolve_encoding_config()
        wm_name = globals().get("Watermark_Name", "")

        ffcmd = [resolve_executable("ffmpeg", ffmpeg_path), "-nostdin", "-y", "-i", dec_video]
        for a in audio_files:
            ffcmd += ["-i", a["path"]]
        for s in subtitle_files:
            ffcmd += ["-i", s["path"]]

        map_args  = []
        meta_args = []

        if enc_cfg.use_watermark:
            ffcmd += ["-filter_complex", get_filter_complex()]
            map_args += ["-map", "[v]"]
        else:
            map_args += ["-map", "0:v?"]

        for i, a in enumerate(audio_files):
            map_args += ["-map", f"{i + 1}:a?"]
            lc = LANGUAGE_NAME_TO_ISO639_2B.get(a["title_lang"], a["title_lang"]) or "und"
            tl = a["title_lang"]
            meta_args += [f"-metadata:s:a:{i}", f"language={lc}", f"-metadata:s:a:{i}", f'title=[{tl}]']

        for i, s in enumerate(subtitle_files):
            map_args += ["-map", f"{len(audio_files) + i + 1}:s?"]
            lc = LANGUAGE_NAME_TO_ISO639_2B.get(s["title_lang"], s["title_lang"]) or "und"
            tl = s["title_lang"]
            meta_args += [f"-metadata:s:s:{i}", f"language={lc}", f"-metadata:s:s:{i}", f'title=[{tl}]']

        q_str  = f"{video_quality_info['height']}p"
        a_str  = "+".join(a["title_lang"] for a in audio_files) or "NoAudio"
        s_str  = "+".join(s["title_lang"] for s in subtitle_files) or "NoSubs"
        wm_sfx = f".{wm_name}" if enc_cfg.use_watermark else ""

        out_file = f"{base_path}.{q_str}.[{a_str}].[{s_str}]{wm_sfx}.{output_format}"

        ffcmd += map_args + meta_args + enc_cfg.get_ffmpeg_args_list() + [out_file]
        edit_message(status_msg, f"{progress_prefix}⚙  「 Merging... this may take a few minutes. 」\n`{out_file}`")

        _, stderr, rc = run_shell_command(ffcmd)
        if rc != 0:
            log = f"{base_path}_ffmpeg_error.log"
            with open(log, "w") as f:
                f.write(f"Command: {display_command(ffcmd)}\n\n{stderr}")
            raise Exception(f"FFmpeg failed. See {log}")

        return out_file

    except Exception as e:
        traceback.print_exc()
        edit_message(status_msg, f"{progress_prefix}" + UI["error"].format(error=e))
        return None


def cleanup_files(paths):
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        try:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p, topdown=False):
                    for f in files:
                        os.remove(os.path.join(root, f))
                    for d in dirs:
                        os.rmdir(os.path.join(root, d))
                os.rmdir(p)
            else:
                os.remove(p)
        except OSError as e:
            print(f"Cleanup error ({p}): {e}")
    td = get_temp_path()
    if os.path.exists(td) and not os.listdir(td):
        with suppress(OSError):
            os.rmdir(td)


if __name__ == "__main__":
    print("[CrunchyBot] Starting…")
    app.run()
    print("[CrunchyBot] Stopped.")
