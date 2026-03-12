"""
=============================================================
  מוניטור סוריה — Syria Intelligence Monitor + תרגום AI
=============================================================
• מנטר 60+ ערוצי טלגרם בערבית, אנגלית, רוסית
• מתרגם כל פרסום לעברית דרך Claude AI
• התראה מיידית על כל אזכור ישראל
• דוח יומי + סיכום מודיעיני אוטומטי

דרישות:
  pip install telethon python-telegram-bot schedule python-dotenv anthropic
=============================================================
"""

import asyncio, os, json, logging, schedule, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient
from telegram import Bot
from telegram.constants import ParseMode
import anthropic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("syria_monitor.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)
load_dotenv()

API_ID        = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH      = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN     = os.getenv("BOT_TOKEN", "")
MY_CHAT_ID    = os.getenv("MY_CHAT_ID", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ═══════════════════════════════════════════════════════════
#  ערוצים לנטר
# ═══════════════════════════════════════════════════════════
CHANNELS = [

    # ── ערוצים סוריים — ידיעות מהשטח ──────────────────────
    "@SyrianCivilWarMap",
    "@Syria_news_ar",
    "@step_agency_ar",
    "@syria_direct_ar",
    "@Souria4Syrians",
    "@suwayda24",
    "@Daraa24_ar",
    "@Deir_Ezzor_24",
    "@AleppoToday",
    "@hama_news_sy",
    "@Idlib_news_ar",
    "@Damascus_news_ar",
    "@QasiounNews",
    "@enabbaladi",
    "@syriahr",
    "@SANA_English",
    "@Zaman_AlWasl",
    "@orient_news_sy",

    # ── HTS וכוחות שחרור ────────────────────────────────────
    "@fajr_news_sy",
    "@ibaa_agency",

    # ── SDF/AANES ───────────────────────────────────────────
    "@ANFNewsArabic",
    "@hawar_news_ar",
    "@ANHA_agency",

    # ── תקשורת מערבית שמכסה סוריה ──────────────────────────
    "@BBCArabic",
    "@AlJazeeraEnglish",
    "@AlJazeeraSyria",
    "@alarabiya_ar",
    "@skynewsarabia",
    "@middleeasteye",
    "@france24_ar",
    "@DW_Arabic",

    # ── OSINT וניתוח צבאי ──────────────────────────────────
    "@IntelSlava",
    "@OSINTdefender",
    "@sentdefender",
    "@GeoConfirmed",
    "@Aurora_intel",
    "@warmonitor1",
    "@conflictnews",
    "@militarylandnet",
    "@TheDeadDistrict",
    "@rybar_en",
    "@airwars_org",
    "@oryx_blog",

    # ── מדיני ───────────────────────────────────────────────
    "@MiddleEastSpectator",

    # ── איראן וחיזבאללה ─────────────────────────────────────
    "@PressTV_Arabic",
    "@AlManarTV",
    "@mayadeen_news",

    # ── רוסיה ───────────────────────────────────────────────
    "@rybar",
    "@WarGonzo",
    "@milinfolive",
]

# ═══════════════════════════════════════════════════════════
#  מילות מפתח
# ═══════════════════════════════════════════════════════════

ISRAEL_KEYWORDS = [
    "إسرائيل", "الجيش الإسرائيلي", "غارة إسرائيلية", "القوات الإسرائيلية",
    "تل أبيب", "الموساد", "سلاح الجو الإسرائيلي", "إسرائيلي", "إسرائيلية",
    "Israel", "IDF", "Israeli", "Tel Aviv", "Mossad", "IAF",
    "ישראל", "צה\"ל", "מוסד",
    "Израиль", "израильский",
]

MILITARY_KEYWORDS = [
    "عملية عسكرية", "تقدم الجيش", "غارة جوية", "مسيّرة", "طائرة مسيرة",
    "صواريخ", "مدفعية", "دبابات", "قوات مسلحة", "معارك", "اشتباكات",
    "منظومة دفاع جوي", "قاعدة عسكرية", "مستودع ذخيرة", "تعزيزات",
    "انتشار عسكري", "هجوم", "قصف", "ميليشيا", "فصائل مسلحة",
    "الحرس الثوري", "حزب الله", "قوات خاصة", "استخبارات", "أسلحة",
    "airstrike", "military operation", "offensive", "drone", "UAV",
    "missile", "artillery", "tank", "troops", "attack", "weapons",
    "IRGC", "Hezbollah", "special forces",
]

POLITICAL_KEYWORDS = [
    "مفاوضات", "اتفاقية", "تطبيع", "علاقات دبلوماسية", "وزير خارجية",
    "عقوبات", "رفع العقوبات", "إعادة الإعمار", "اللاجئين",
    "الأمم المتحدة", "مجلس الأمن", "جامعة الدول العربية",
    "sanctions", "diplomacy", "negotiations", "reconstruction", "UN",
]

SYRIA_KEYWORDS = [
    "سوريا", "سورية", "السوري", "دمشق", "حلب", "إدلب", "حماة", "حمص",
    "درعا", "دير الزور", "الرقة", "الحسكة", "هيئة تحرير الشام",
    "قوات سوريا الديمقراطية", "الجولاني", "الشرع",
    "Syria", "Syrian", "Damascus", "Aleppo", "Idlib", "HTS", "SDF",
]


def find_matches(text: str) -> dict:
    t = text.lower()
    return {
        "israel":    [k for k in ISRAEL_KEYWORDS    if k.lower() in t],
        "military":  [k for k in MILITARY_KEYWORDS  if k.lower() in t],
        "political": [k for k in POLITICAL_KEYWORDS if k.lower() in t],
        "syria":     [k for k in SYRIA_KEYWORDS     if k.lower() in t],
    }


def is_relevant(m: dict) -> bool:
    return bool(m["israel"]) or (bool(m["syria"]) and bool(m["military"] or m["political"]))


def is_israel_alert(m: dict) -> bool:
    return bool(m["israel"])


# ═══════════════════════════════════════════════════════════
#  תרגום + סיכום AI
# ═══════════════════════════════════════════════════════════

async def translate_to_hebrew(text: str, channel: str = "") -> str:
    try:
        text_in = text[:1500]
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content":
                f"אתה מתרגם מומחה לענייני ביטחון ומזרח תיכון.\n"
                f"תרגם לעברית בצורה מדויקת ומקצועית. שמור על מונחים צבאיים נכונים.\n"
                f"{'ערוץ המקור: ' + channel if channel else ''}\n\n"
                f"טקסט לתרגום:\n{text_in}\n\nתרגום לעברית בלבד:"
            }]
        )
        return response.content[0].text.strip()
    except Exception as e:
        log.error(f"שגיאת תרגום: {e}")
        return f"[לא ניתן לתרגם] {text[:200]}"


async def ai_daily_summary(results: list[dict]) -> str:
    try:
        posts = "\n".join(
            f"- [{r['channel_title']}] {r['text'][:300]}"
            for r in results[:25]
        )
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content":
                f"אתה אנליסט מודיעיני מומחה לסוריה. תאריך: {datetime.now().strftime('%d/%m/%Y')}.\n"
                f"להלן פרסומים מערוצי טלגרם שנאספו היום:\n\n{posts}\n\n"
                f"כתוב בריפינג מודיעיני קצר בעברית:\n"
                f"1. 🔴 האירועים הצבאיים המשמעותיים\n"
                f"2. 🏛 ההתפתחויות המדיניות\n"
                f"3. 🎯 למה הכוחות מתכוננים\n"
                f"4. ⚠️ נקודות תשומת לב מיוחדות\n"
                f"סגנון: תמציתי ומקצועי."
            }]
        )
        return response.content[0].text.strip()
    except Exception as e:
        log.error(f"שגיאת סיכום: {e}")
        return "לא ניתן לייצר סיכום אוטומטי."


# ═══════════════════════════════════════════════════════════
#  שליחת הודעות
# ═══════════════════════════════════════════════════════════

async def send_israel_alert(bot: Bot, result: dict):
    log.info(f"🚨 התראת ישראל: {result['channel_title']}")
    translation = await translate_to_hebrew(result["text"], result["channel_title"])
    msg = (
        f"🚨🚨 *התראה מיידית — אזכור ישראל*\n"
        f"{'═' * 32}\n"
        f"📡 *ערוץ:* {result['channel_title']}\n"
        f"🕐 *זמן:* {result['date']}\n"
        f"🔗 [פרסום מקורי]({result['link']})\n\n"
        f"📝 *תרגום:*\n{translation}\n\n"
        f"🏷 *זוהה:* {', '.join(result['matches']['israel'][:4])}"
    )
    try:
        await bot.send_message(chat_id=MY_CHAT_ID, text=msg[:4096],
                               parse_mode=ParseMode.MARKDOWN,
                               disable_web_page_preview=True)
    except Exception as e:
        log.error(f"שגיאה: {e}")
        await bot.send_message(chat_id=MY_CHAT_ID, text=msg[:4000])


async def send_daily_report(bot: Bot, results: list[dict]):
    if not results:
        await bot.send_message(
            chat_id=MY_CHAT_ID,
            text=f"✅ *דוח יומי — {datetime.now().strftime('%d/%m/%Y')}*\n\nלא נמצאו פרסומים רלוונטיים.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    israel_n   = sum(1 for r in results if r["matches"]["israel"])
    military_n = sum(1 for r in results if r["matches"]["military"])
    political_n= sum(1 for r in results if r["matches"]["political"])

    log.info("מייצר סיכום AI...")
    summary = await ai_daily_summary(results)

    # הודעה 1 — כותרת + סיכום
    header = (
        f"📊 *דוח מודיעיני יומי — סוריה*\n"
        f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"{'═' * 32}\n"
        f"🚨 אזכורי ישראל: *{israel_n}*\n"
        f"⚔️ פרסומים צבאיים: *{military_n}*\n"
        f"🏛 פרסומים מדיניים: *{political_n}*\n"
        f"📰 סה\"כ: *{len(results)}*\n"
        f"{'─' * 32}\n\n"
        f"🧠 *ניתוח מודיעיני — AI:*\n{summary}"
    )
    await bot.send_message(chat_id=MY_CHAT_ID, text=header[:4096],
                           parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(2)

    # הודעות 2+ — פרסומים מתורגמים (מקסימום 15)
    top = sorted(results, key=lambda r: (
        2 if r["matches"]["israel"] else
        1 if r["matches"]["military"] else 0
    ), reverse=True)[:15]

    log.info(f"מתרגם {len(top)} פרסומים...")
    current = "📋 *פרסומים מתורגמים:*\n\n"

    for i, r in enumerate(top, 1):
        icon = "🚨" if r["matches"]["israel"] else \
               "⚔️" if r["matches"]["military"] else "🏛"
        translation = await translate_to_hebrew(r["text"], r["channel_title"])
        short = translation[:320] + ("..." if len(translation) > 320 else "")

        entry = (
            f"{icon} *{i}. {r['channel_title']}*\n"
            f"🕐 {r['date']} | 🔗 [מקור]({r['link']})\n"
            f"{short}\n"
            f"{'─' * 28}\n\n"
        )

        if len(current) + len(entry) > 3800:
            await bot.send_message(chat_id=MY_CHAT_ID, text=current,
                                   parse_mode=ParseMode.MARKDOWN,
                                   disable_web_page_preview=True)
            await asyncio.sleep(1)
            current = entry
        else:
            current += entry

        await asyncio.sleep(0.5)

    if current.strip():
        await bot.send_message(chat_id=MY_CHAT_ID, text=current,
                               parse_mode=ParseMode.MARKDOWN,
                               disable_web_page_preview=True)


# ═══════════════════════════════════════════════════════════
#  סריקה ראשית
# ═══════════════════════════════════════════════════════════

def load_seen_ids() -> set:
    try:
        with open("seen_ids.json") as f:
            return set(json.load(f).get("ids", []))
    except FileNotFoundError:
        return set()


def save_seen_ids(seen: set):
    with open("seen_ids.json", "w") as f:
        json.dump({"ids": list(seen)[-20000:],
                   "last_run": datetime.now().isoformat()}, f)


async def scan_and_report():
    log.info("=" * 50)
    log.info("מתחיל סריקה...")
    seen_ids = load_seen_ids()
    since    = datetime.now() - timedelta(hours=24)
    results  = []
    bot      = Bot(token=BOT_TOKEN)

    async with TelegramClient("syria_session", API_ID, API_HASH) as client:
        for channel in CHANNELS:
            try:
                log.info(f"סורק: {channel}")
                entity = await client.get_entity(channel)

                async for message in client.iter_messages(entity):
                    if message.date.replace(tzinfo=None) < since:
                        break

                    uid = f"{channel}_{message.id}"
                    if uid in seen_ids:
                        continue
                    seen_ids.add(uid)

                    text = message.text or message.caption or ""
                    if len(text) < 20:
                        continue

                    matches = find_matches(text)
                    if not is_relevant(matches):
                        continue

                    username = getattr(entity, "username", None)
                    link = (f"https://t.me/{username}/{message.id}"
                            if username else
                            f"https://t.me/c/{entity.id}/{message.id}")

                    result = {
                        "channel_title": getattr(entity, "title", channel),
                        "text": text,
                        "date": message.date.strftime("%d/%m/%Y %H:%M"),
                        "link": link,
                        "matches": matches,
                    }
                    results.append(result)

                    if is_israel_alert(matches):
                        await send_israel_alert(bot, result)

            except Exception as e:
                log.error(f"שגיאה ב-{channel}: {e}")

    save_seen_ids(seen_ids)
    log.info(f"סריקה הושלמה — {len(results)} פרסומים.")
    await send_daily_report(bot, results)


# ═══════════════════════════════════════════════════════════
#  הפעלה
# ═══════════════════════════════════════════════════════════

def run():
    asyncio.run(scan_and_report())


def main():
    import sys
    if "--once" in sys.argv:
        run()
        return

    run_time = os.getenv("DAILY_RUN_TIME", "07:00")
    log.info(f"מתזמן הרצה יומית בשעה {run_time}")
    schedule.every().day.at(run_time).do(run)
    run()
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
