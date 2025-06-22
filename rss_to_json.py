import feedparser
import json
from datetime import datetime, timezone, timedelta
import time
import sys
import re # هذا import ضروري لدالة clean_html

# **مهم جدًا:** ضبط ترميز الإخراج لضمان عرض الأحرف العربية بشكل صحيح في الطرفية.
# هذا يعالج مشكلة UnicodeEncodeError.
sys.stdout.reconfigure(encoding='utf-8')

# --- إعداداتك ---
# قائمة بتغذيات RSS التي ترغب في سحب الأخبار منها.
# يمكنك إضافة أو إزالة الروابط حسب الحاجة.
RSS_FEEDS = [
    "https://al3omk.com/feed",
    "https://www.hespress.com/feed",
    "https://assabah.ma/feed",
    "https://alaan.ma/?feed=rss2",
    "https://rue20.com/feed",
    "https://www.almaghreb24.com/feed/",
    "https://alyaoum24.com/feed",
    "https://aljarida24.ma/feed/",
    "https://www.alakhbar.press.ma/feed",
    "https://www.assahifa.com/feed/", # تأكد من الرابط الصحيح: بعض الروابط قد تحتاج لـ / في النهاية
    "https://madar21.com/feed",
    "https://howiyapress.com/feed/",
    "https://banassa.info/feed/",
    "https://almap.press/feed/",
    "https://ar.hibapress.com/feed",
    "https://www.almountakhab.com/sitemap-rss.rss",
    "https://www.achkayen.com/feed",
    "https://maroc28.ma/feed/",
    "https://presstetouan.com/feed/",
    "https://tangerpress.com/feed",
    "https://tanja24.com/feed",
    "https://ecopress.ma/feed/",
    "https://www.tanja7.com/feed/",
    "https://chamaly.ma/home/feed/",
    "https://laracheinfo.com/feed",
    "https://nichan.ma/feed/"
]

# اسم متجرك (يتم سحبه من معلوماتك المحفوظة).
STORE_NAME = "hachimi shop"

# مسار حفظ ملف JSON الذي سيتم عرضه بواسطة صفحة الويب.
# تأكد أن هذا الملف موجود في نفس المجلد مع index.html (أو index.php).
OUTPUT_JSON_FILE = "articles.json"

def get_published_datetime(entry):
    """
    يحاول الحصول على كائن datetime من تاريخ النشر.
    يتعامل مع تنسيقات مختلفة لتاريخ النشر الشائعة في RSS.
    """
    # الخيار الأول: استخدام published_parsed الذي توفره feedparser
    if 'published_parsed' in entry and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except TypeError:
            pass # قد يكون published_parsed غير مكتمل، ننتقل للخيار التالي

    # الخيار الثاني: محاولة تحليل حقل 'published' كنص
    if 'published' in entry and entry.published:
        published_str = entry.published.strip()
        
        # تنسيق ISO 8601 شائع (مثال: 2024-06-21T10:00:00Z)
        if 'T' in published_str and ('Z' in published_str or '+' in published_str or '-' in published_str):
            try:
                # استبدال Z بـ +00:00 ليتوافق مع fromisoformat بشكل أفضل
                return datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # تنسيق RFC 822/2822 (مثال: Fri, 21 Jun 2024 10:00:00 +0000)
        try:
            return datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            pass
        
        # تنسيقات أخرى قديمة أو أقل شيوعًا (يمكن إضافة المزيد هنا إذا لزم الأمر)
        try:
            return datetime.strptime(published_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
        try:
            return datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass

    # إذا فشلت جميع المحاولات، نرجع تاريخًا قديمًا جدًا لفرزها في النهاية
    return datetime.min.replace(tzinfo=timezone.utc)

def clean_html(raw_html):
    """يزيل وسوم HTML الأساسية من النصوص."""
    # يمكن استخدام مكتبات مثل BeautifulSoup لتنظيف أكثر شمولاً،
    # لكن هذا يكفي لمعظم الحالات البسيطة.
    cleanr = re.compile('<.*?>|&nbsp;')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def fetch_and_save_news():
    """يسحب الأخبار من تغذيات RSS ويحفظها في ملف JSON."""
    all_articles = []
    print(f"أهلاً بك في نظام أخبار {STORE_NAME}")
    print(f"جاري جلب الأخبار من {len(RSS_FEEDS)} مصادر... قد يستغرق هذا بعض الوقت.")

    for feed_url in RSS_FEEDS:
        print(f"جاري جلب الأخبار من: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            # الحصول على اسم المصدر من التغذية نفسها، أو قيمة افتراضية
            source_title = feed.feed.get('title', 'مصدر غير معروف').strip()
            if not source_title: # في حال كان العنوان فارغاً
                source_title = feed_url.split('//')[-1].split('/')[0] # أخذ الدومين كاسم مصدر

            for entry in feed.entries:
                title = entry.get('title', 'عنوان غير متوفر').strip()
                link = entry.get('link', '#').strip()
                published_dt = get_published_datetime(entry)
                summary = entry.get('summary', 'ملخص غير متوفر').strip()
                
                # تنظيف الملخص باستخدام الدالة المخصصة
                clean_summary = clean_html(summary)

                article_data = {
                    "title": title,
                    "link": link,
                    "published": published_dt.isoformat(), # حفظ التاريخ بتنسيق ISO 8601 لسهولة التحويل لاحقاً
                    "summary": clean_summary,
                    "source": source_title
                }
                all_articles.append(article_data)
        except Exception as e:
            print(f"خطأ في سحب التغذية من {feed_url}: {e}")
            continue # الاستمرار في التغذيات الأخرى حتى لو فشلت إحداها

    # فرز جميع المقالات حسب تاريخ النشر (الأحدث أولاً)
    all_articles.sort(key=lambda x: datetime.fromisoformat(x['published']), reverse=True)

    # حفظ المقالات في ملف JSON
    try:
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=4)
        print(f"\nتم حفظ {len(all_articles)} مقالاً في {OUTPUT_JSON_FILE}")
    except Exception as e:
        print(f"خطأ في حفظ ملف JSON: {e}")

if __name__ == "__main__":
    fetch_and_save_news()
    # لتحديث الأخبار تلقائيًا، يجب جدولة تشغيل هذا السكربت بانتظام
    # (مثلاً، باستخدام Cron Job على Linux/macOS أو Task Scheduler على Windows).
