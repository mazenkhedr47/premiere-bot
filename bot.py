import os
import time
from playwright.sync_api import sync_playwright
import requests

# السيرفر هيقرأ التوكن والأيدي من إعدادات الأمان في جيت هاب
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

URL = "https://www.premiere-cinemas.com/en"
MOVIE_KEYWORDS = ["doomsday", "dooms day"]
CINEMA_KEYWORDS = ["plaza", "americana"]


def send_telegram_alert(message):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message}
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"خطأ في إرسال رسالة تليجرام: {e}")


def check_premiere_tickets():
  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    try:
      print("جاري فحص موقع Premiere Cinemas...")
      page.goto(URL, timeout=60000, wait_until="networkidle")
      page.wait_for_timeout(5000)

      page_content = page.inner_text("body").lower()
      movie_found = any(keyword in page_content for keyword in MOVIE_KEYWORDS)

      if movie_found:
        print("الفيلم ظهر! جاري فحص فتح الحجز وفرع بلازا...")
        links = page.locator("a").all()
        movie_url = None
        for link in links:
          text = (link.inner_text() or "").lower()
          href = link.get_attribute("href") or ""
          if any(k in text for k in MOVIE_KEYWORDS) or any(
              k in href.lower() for k in MOVIE_KEYWORDS
          ):
            if href.startswith("http"):
              movie_url = href
            elif href.startswith("/"):
              movie_url = "https://www.premiere-cinemas.com" + href
            break

        if movie_url:
          page.goto(movie_url, timeout=60000, wait_until="networkidle")
          page.wait_for_timeout(4000)
          movie_page_text = page.inner_text("body").lower()

          plaza_found = any(k in movie_page_text for k in CINEMA_KEYWORDS)
          booking_active = (
              "book now" in movie_page_text
              or "showtimes" in movie_page_text
              or "pm" in movie_page_text
              or "am" in movie_page_text
          )

          if plaza_found and booking_active:
            send_telegram_alert(
                "🚨 الحق احجز حالاً!\nتذاكر فيلم Doomsday نزلت في فرع Premiere"
                f" Plaza!\n\nرابط الحجز المباشر:\n{movie_url}"
            )
          else:
            print(
                "الفيلم موجود على الموقع بس لسه الحجز مفتحش في فرع بلازا."
            )
        else:
          if any(k in page_content for k in CINEMA_KEYWORDS) and (
              "book" in page_content
          ):
            send_telegram_alert(
                "🚨 فيلم Doomsday ظهر على موقع Premiere Cinemas!\nادخل شيك على"
                f" الحجز دلوقتي:\n{URL}"
            )
      else:
        print("الفيلم لسه منزلش في قائمة الحجز...")

    except Exception as e:
      print(f"حصل خطأ أثناء التحميل: {e}")

    browser.close()


if __name__ == "__main__":
  check_premiere_tickets()
