"""
Syria Intelligence Monitor Bot — ללא תרגום
"""
import asyncio, os, json, logging, schedule, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient
from telegram import Bot
from telegram.constants import ParseMode

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

API_ID     = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH   = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN  = os.getenv("BOT_TOKEN", "")
MY_CHAT_ID = os.getenv("MY_CHAT_ID", "")

CHANNELS = [
    # ── ערוצים סוריים מהשטח — רשימה מקורית ──────────────
    "@SyrianCivilWarMap", "@Syria_news_ar", "@step_agency_ar",
    "@syria_direct_ar", "@Souria4Syrians", "@suwayda24",
    "@Daraa24_ar", "@Deir_Ezzor_24", "@AleppoToday",
    "@hama_news_sy", "@Idlib_news_ar", "@Damascus_news_ar",
    "@QasiounNews", "@enabbaladi", "@syriahr", "@SANA_English",
    "@Zaman_AlWasl", "@orient_news_sy", "@fajr_news_sy",
    "@ANFNewsArabic", "@hawar_news_ar",

    # ── ערוצים סוריים חדשים — מהרשימה שלך ───────────────
    "@Lattakia_Alekhbariah",   # اللاذقية الإخبارية
    "@AbdAlhadyridwan1",       # الإعلامي عبد الهادي رضوان
    "@marsadalshamall",        # مرصد تحرير سوريا
    "@Field_surveyor",         # مراسل ميداني
    "@Adham_Damascus",         # أدهم الأيوبي - دمشق
    "@ttasit",                 # ثورة الشام
    "@waelo10",                # عواد wael
    "@Qatada23",               # قتادة - سوريا
    "@ABD963ALRHMAN",          # عبدالرحمن الشغري
    "@Qusaialmasre",           # قصي المصري
    "@ammamai",                # ערוץ סורי
    "@Sada_Defense",           # صدى الدفاع
    "@skksb108",               # ערוץ סורי
    "@sayfallahalumawiu",      # سيف الله الأموي
    "@muhaand19",              # الإعلامي مهند قيراطة
    "@MOATSEM_ALAHMAD",        # معتصم الأحمد
    "@askerioperasyonn",       # ערוץ צבאי
    "@syrianevent1",           # أحداث سوريا
    "@khalil124kh",            # ערוץ סורי
    "@tvsham",                 # تلفزيون الشام
    "@jisralshughur",          # جسر الشغور
    "@howaboutoutm",           # ערוץ סורי
    "@syria_2025",             # سوريا 2025
    "@DiyaaSyria",             # ضياء سوريا
    "@mou2027",                # ערוץ סורי
    "@manbij_1",               # منبج
    "@muhamad_200",            # ערוץ סורי

    # ── תקשורת מערבית ────────────────────────────────────
    "@BBCArabic", "@AlJazeeraEnglish", "@AlJazeeraSyria",
    "@alarabiya_ar", "@skynewsarabia", "@middleeasteye",
    "@france24_ar", "@DW_Arabic",

    # ── OSINT וניתוח צבאי ────────────────────────────────
    "@IntelSlava", "@OSINTdefender", "@sentdefender",
    "@GeoConfirmed", "@Aurora_intel", "@warmonitor1",
    "@conflictnews", "@militarylandnet", "@TheDeadDistrict",
    "@rybar_en", "@airwars_org", "@oryx_blog",
    "@MiddleEastSpectator",

    # ── איראן/חיזבאללה/רוסיה ─────────────────────────────
    "@PressTV_Arabic", "@AlManarTV", "@mayadeen_news",
    "@rybar", "@WarGonzo", "@milinfolive",
]

# ── ישראל — רק איך הסורים מדברים עליה בינם לבין עצמם ──
ISRAEL_KEYWORDS = [
    # עמדות וריאקציות סוריות על ישראל
    "الموقف من إسرائيل", "تطبيع مع إسرائيل", "التطبيع مع إسرائيل",
    "الكيان الصهيوني", "الصهاينة", "فلسطين وسوريا",
    "العلاقة مع إسرائيل", "إسرائيل والجولان", "الجولان السوري",
    "الحدود مع إسرائيل", "الجبهة الجنوبية", "درعا وإسرائيل",
    "normalization with Israel", "Golan Heights Syria",
    "Syrian stance on Israel", "southern front Israel",
]

# ── צבאי — מבנה, פריסה, יכולות של הצבא הסורי החדש ──
MILITARY_KEYWORDS = [
    # מבנה כוחות ופיקוד
    "وزارة الدفاع السورية", "الجيش الوطني السوري", "هيئة الأركان",
    "تعيين قائد", "إعادة هيكلة الجيش", "دمج الفصائل",
    "الفصائل المسلحة", "قوات الأمن الجديدة", "وزير الدفاع",
    "الشرطة العسكرية", "الاستخبارات العسكرية",
    # נשק וציוד
    "أسلحة ثقيلة", "دبابات", "مدفعية", "طائرات مسيرة",
    "منظومة صواريخ", "ذخيرة", "مستودع أسلحة",
    # תרגילים ומבצעים פנימיים
    "تدريبات عسكرية", "انتشار قوات", "عملية أمنية",
    "مكافحة الإرهاب", "داعش سوريا", "خلايا نائمة",
    # אנגלית
    "Syrian army restructure", "HTS military", "new Syrian army",
    "Syrian defense ministry", "armed factions merge",
    "ISIS Syria", "sleeper cells Syria",
]

# ── פנים סוריה — פוליטיקה, דת, חברה ──
INTERNAL_KEYWORDS = [
    # פוליטיקה פנימית
    "الحكومة السورية الجديدة", "أحمد الشرع", "الجولاني",
    "المعارضة السورية", "مجلس الحكم", "الدستور السوري",
    "الانتخابات السورية", "اللامركزية", "إدارة المناطق",
    "الخلاف بين الفصائل", "التوترات الداخلية",
    # דת ואידיאולוגיה
    "الشريعة الإسلامية في سوريا", "الأقليات الدينية",
    "العلويون", "الدروز سوريا", "المسيحيون سوريا",
    "السنة والشيعة سوريا", "الإسلام المعتدل سوريا",
    "هيئة العلماء", "فتوى سوريا", "الحرية الدينية سوريا",
    # חברה וכלכלה
    "إعادة الإعمار", "عودة اللاجئين", "الاقتصاد السوري",
    "البطالة سوريا", "الفقر سوريا", "الخدمات الأساسية",
    "الكهرباء سوريا", "المناطق المحررة", "المصالحة الوطنية",
    # אנגלית
    "new Syrian government", "Ahmed al-Sharaa", "Syria constitution",
    "Syrian minorities", "Alawites Syria", "Druze Syria",
    "Christians Syria", "Syria reconstruction", "Syrian economy",
    "sectarian Syria", "religious freedom Syria",
]

SYRIA_KEYWORDS = [
    "سوريا", "سورية", "السوري", "السورية", "دمشق", "حلب", "إدلب",
    "حماة", "حمص", "درعا", "دير الزور", "الرقة", "الحسكة",
    "هيئة تحرير الشام", "قوات سوريا الديمقراطية",
    "Syria", "Syrian", "Damascus", "Aleppo", "Idlib", "HTS", "SDF",
]


def find_matches(text):
    t = text.lower()
    return {
        "israel":   [k for k in ISRAEL_KEYWORDS   if k.lower() in t],
        "military": [k for k in MILITARY_KEYWORDS if k.lower() in t],
        "internal": [k for k in INTERNAL_KEYWORDS if k.lower() in t],
        "syria":    [k for k in SYRIA_KEYWORDS    if k.lower() in t],
    }


def is_relevant(m):
    # חייב להיות קשור לסוריה + תוכן רלוונטי
    has_syria = bool(m["syria"])
    has_content = bool(m["israel"] or m["military"] or m["internal"])
    return has_syria and has_content


def is_israel_alert(m):
    # התראה רק כשסורים מדברים על ישראל בהקשר סורי
    return bool(m["israel"]) and bool(m["syria"])


async def send_israel_alert(bot, result):
    log.info(f"🚨 התראת ישראל: {result['channel_title']}")
    text_preview = result["text"][:500]
    msg = (
        f"🚨🚨 *התראה מיידית — אזכור ישראל*\n"
        f"{'═' * 30}\n"
        f"📡 *ערוץ:* {result['channel_title']}\n"
        f"🕐 *זמן:* {result['date']}\n"
        f"🔗 [פרסום מקורי]({result['link']})\n\n"
        f"📝 *תוכן:*\n{text_preview}\n\n"
        f"🏷 *זוהה:* {', '.join(result['matches']['israel'][:4])}"
    )
    try:
        await bot.send_message(chat_id=MY_CHAT_ID, text=msg[:4096],
                               parse_mode=ParseMode.MARKDOWN,
                               disable_web_page_preview=True)
    except Exception as e:
        log.error(f"שגיאה: {e}")
        await bot.send_message(chat_id=MY_CHAT_ID, text=msg[:4000])


async def send_daily_report(bot, results):
    if not results:
        await bot.send_message(
            chat_id=MY_CHAT_ID,
            text=f"✅ *דוח יומי — {datetime.now().strftime('%d/%m/%Y')}*\n\nלא נמצאו פרסומים רלוונטיים.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    israel_n   = sum(1 for r in results if r["matches"]["israel"])
    military_n = sum(1 for r in results if r["matches"]["military"])
    internal_n = sum(1 for r in results if r["matches"]["internal"])

    header = (
        f"📊 *דוח יומי — סוריה מבפנים*\n"
        f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"{'═' * 30}\n"
        f"🚨 ישראל בעיני הסורים: *{israel_n}*\n"
        f"⚔️ צבאי/ביטחוני: *{military_n}*\n"
        f"🕌 פוליטי/דתי/חברתי: *{internal_n}*\n"
        f"📰 סה\"כ: *{len(results)}*\n"
    )
    await bot.send_message(chat_id=MY_CHAT_ID, text=header,
                           parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(1)

    current = ""
    for i, r in enumerate(results[:30], 1):
        icon = "🚨" if r["matches"]["israel"] else \
               "⚔️" if r["matches"]["military"] else "🕌"
        text_short = r["text"][:200] + ("..." if len(r["text"]) > 200 else "")
        entry = (
            f"{icon} *{i}. {r['channel_title']}* | {r['date']}\n"
            f"{text_short}\n"
            f"🔗 [קישור]({r['link']})\n\n"
        )
        if len(current) + len(entry) > 3800:
            await bot.send_message(chat_id=MY_CHAT_ID, text=current,
                                   parse_mode=ParseMode.MARKDOWN,
                                   disable_web_page_preview=True)
            await asyncio.sleep(1)
            current = entry
        else:
            current += entry

    if current.strip():
        await bot.send_message(chat_id=MY_CHAT_ID, text=current,
                               parse_mode=ParseMode.MARKDOWN,
                               disable_web_page_preview=True)


def load_seen_ids():
    try:
        with open("seen_ids.json") as f:
            return set(json.load(f).get("ids", []))
    except FileNotFoundError:
        return set()


def save_seen_ids(seen):
    with open("seen_ids.json", "w") as f:
        json.dump({"ids": list(seen)[-20000:],
                   "last_run": datetime.now().isoformat()}, f)


async def scan_and_report():
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

