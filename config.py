"""
config.py — All settings are loaded from environment variables for Railway.
Set these in Railway → Service → Variables tab.
"""
import os

# ── Crunchyroll Account ──────────────────────────────────────
use_account          = os.environ.get("CR_USE_ACCOUNT", "true").lower() == "true"
Email                = os.environ.get("CR_EMAIL", "")
Password             = os.environ.get("CR_PASSWORD", "")
etp_rt_token         = os.environ.get("CR_ETP_RT_TOKEN", "")
allow_guest_fallback = os.environ.get("CR_GUEST_FALLBACK", "false").lower() == "true"

# ── Telegram ─────────────────────────────────────────────────
API_ID    = int(os.environ.get("TG_API_ID", "0"))
API_HASH  = os.environ.get("TG_API_HASH", "")
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")

# ── User Management ──────────────────────────────────────────
def _parse_id_list(env_key: str):
    raw = os.environ.get(env_key, "")
    return [int(x.strip()) for x in raw.split(",") if x.strip().lstrip("-").isdigit()]

sudo_users       = _parse_id_list("SUDO_USERS")
premium_users    = _parse_id_list("PREMIUM_USERS")
AUTHORIZED_USERS = _parse_id_list("AUTHORIZED_USERS")

# ── Limits ───────────────────────────────────────────────────
REGULAR_USER_AUDIO_LIMIT   = int(os.environ.get("REGULAR_AUDIO_LIMIT", "2"))
REGULAR_USER_VIDEO_LIMIT_P = int(os.environ.get("REGULAR_VIDEO_LIMIT_P", "480"))

# ── Bot Runtime State (in-memory) ────────────────────────────
user_states      = {}
active_downloads = {}

# ── Debug ────────────────────────────────────────────────────
debug        = os.environ.get("DEBUG", "false").lower() == "true"
level        = ""
max_retries  = int(os.environ.get("MAX_RETRIES", "3"))
retry_delay  = int(os.environ.get("RETRY_DELAY", "2"))
download_threads = int(os.environ.get("DOWNLOAD_THREADS", "8"))

# ── Proxy ────────────────────────────────────────────────────
use_proxy = os.environ.get("USE_PROXY", "false").lower() == "true"
proxy     = os.environ.get("PROXY_URL", "")

# ── Watermark ────────────────────────────────────────────────
Watermark_Name = os.environ.get("WATERMARK_NAME", "CrunchyBot")
fontfile       = os.environ.get("FONT_FILE", "font.ttf")
fontcolor      = os.environ.get("FONT_COLOR", "white")
opaque         = os.environ.get("FONT_OPACITY", "0.4")
fontsize       = os.environ.get("FONT_SIZE", "h/10")
x_axis         = os.environ.get("WATERMARK_X", "10")
y_axis         = os.environ.get("WATERMARK_Y", "(h-text_h)/2")

# ── Encoding ─────────────────────────────────────────────────
encoding_mode  = os.environ.get("ENCODING_MODE", "lossy")
crf            = int(os.environ.get("CRF", "20"))
preset         = os.environ.get("PRESET", "medium")
pix_fmt        = os.environ.get("PIX_FMT", "yuv420p10le")
encoding_code  = os.environ.get("ENCODING_CODE", "libx265")
audio_codec    = os.environ.get("AUDIO_CODEC", "copy")
output_format  = os.environ.get("OUTPUT_FORMAT", "mkv")
original_quality = os.environ.get("ORIGINAL_QUALITY", "false").lower() == "true"
use_watermark  = os.environ.get("USE_WATERMARK", "true").lower() == "true"
ffmpeg_path    = os.environ.get("FFMPEG_PATH", "ffmpeg")

# ── Custom Title ─────────────────────────────────────────────
use_custom_title = os.environ.get("USE_CUSTOM_TITLE", "false").lower() == "true"
custom_title     = os.environ.get("CUSTOM_TITLE", "{Title} S{Season}E{Episode} - {EpTitle}")

# ── Locale Map ───────────────────────────────────────────────
locale_map = {
    "ja-JP": "Japanese",
    "en-US": "English (US)",
    "de-DE": "German",
    "es-419": "Spanish (Latin America)",
    "es-ES": "Spanish (Spain)",
    "fr-FR": "French",
    "it-IT": "Italian",
    "pt-BR": "Portuguese (Brazil)",
    "hi-IN": "Hindi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "ru-RU": "Russian",
    "ar-SA": "Arabic (Saudi Arabia)",
    "ko-KR": "Korean",
    "vi-VN": "Vietnamese",
    "th-TH": "Thai",
    "ms-MY": "Malay",
    "id-ID": "Indonesian",
    "en-IN": "English (India)",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "pl-PL": "Polish",
    "tr-TR": "Turkish",
    "sv-SE": "Swedish",
    "da-DK": "Danish",
    "no-NO": "Norwegian",
    "fi-FI": "Finnish",
    "cs-CZ": "Czech",
    "sk-SK": "Slovak",
    "nl-NL": "Dutch",
    "ro-RO": "Romanian",
    "bg-BG": "Bulgarian",
    "hr-HR": "Croatian",
    "sr-RS": "Serbian",
    "uk-UA": "Ukrainian",
    "el-GR": "Greek",
    "he-IL": "Hebrew",
    "sw-KE": "Swahili",
    "af-ZA": "Afrikaans",
    "bn-BD": "Bengali",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "pa-IN": "Punjabi",
    "ml-IN": "Malayalam",
    "or-IN": "Odia",
    "as-IN": "Assamese",
    "ur-IN": "Urdu",
    "ta-LK": "Tamil (Sri Lanka)",
    "te-LK": "Telugu (Sri Lanka)",
    "zh-HK": "Chinese (Hong Kong)",
}

LANGUAGE_NAME_TO_ISO639_2B = {
    "Afrikaans": "afr", "Arabic": "ara", "Arabic (Saudi Arabia)": "ara",
    "Assamese": "asm", "Bengali": "ben", "Bulgarian": "bul",
    "Chinese": "zho", "Chinese (Hong Kong)": "zho", "Chinese (Simplified)": "zho",
    "Chinese (Traditional)": "zho", "Croatian": "hrv", "Czech": "ces",
    "Danish": "dan", "Dutch": "nld", "English": "eng", "English (US)": "eng",
    "English (India)": "eng", "Finnish": "fin", "French": "fra",
    "German": "deu", "Greek": "ell", "Gujarati": "guj", "Hebrew": "heb",
    "Hindi": "hin", "Hungarian": "hun", "Indonesian": "ind", "Italian": "ita",
    "Japanese": "jpn", "Kannada": "kan", "Korean": "kor", "Malay": "msa",
    "Malayalam": "mal", "Marathi": "mar", "Norwegian": "nor", "Odia": "ori",
    "Polish": "pol", "Portuguese": "por", "Portuguese (Brazil)": "por",
    "Punjabi": "pan", "Romanian": "ron", "Russian": "rus", "Serbian": "srp",
    "Slovak": "slk", "Spanish": "spa", "Spanish (Spain)": "spa",
    "Spanish (Latin America)": "spa", "Swahili": "swa", "Swedish": "swe",
    "Tamil": "tam", "Tamil (Sri Lanka)": "tam", "Telugu": "tel",
    "Telugu (Sri Lanka)": "tel", "Thai": "tha", "Turkish": "tur",
    "Ukrainian": "ukr", "Urdu": "urd", "Vietnamese": "vie",
}
