import re
import time
import os
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()

# Kredensial yang dicatat langsung di kode (sesuai permintaan user)
ANTAM_USER = "081212149866"
ANTAM_PASS = "nafis2205"

def solve_math(question_text):
    """Menyelesaikan CAPTCHA aritmatika sederhana."""
    match = re.search(r'(\d+)\s+(ditambah|dikurangi|dikali|x)\s+(\d+)', question_text.lower())
    if match:
        num1 = int(match.group(1))
        op = match.group(2)
        num3 = int(match.group(3))
        if op == 'ditambah': return str(num1 + num3)
        elif op == 'dikurangi': return str(num1 - num3)
        elif op in ['dikali', 'x']: return str(num1 * num3)
    return None

def send_telegram_notification(message):
    """Mengirim notifikasi ke Telegram."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, data={"chat_id": chat_id, "text": message})
            logging.info("Notifikasi Telegram terkirim.")
        except Exception as e:
            logging.error(f"Gagal mengirim notifikasi Telegram: {e}")
    else:
        logging.warning("Token Telegram atau Chat ID tidak diatur.")

def check_slots(page):
    """
    Logika untuk mengecek slot antrean setelah login.
    """
    logging.info("Mengecek ketersediaan slot...")
    # Implementasi pengecekan slot bisa ditambahkan di sini
    pass

def run_automation(username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Apply stealth
        stealth_config = Stealth()
        stealth_config.apply_stealth_sync(page)
        
        try:
            logging.info("Membuka halaman login dengan stealth...")
            page.goto("https://antrean.logammulia.com/login", wait_until="domcontentloaded", timeout=60000)
            
            # Tunggu sebentar untuk Cloudflare challenge
            time.sleep(5)
            
            if "challenge" in page.content().lower() or "blocked" in page.content().lower():
                logging.warning("Terdeteksi tantangan Cloudflare. Menunggu lebih lama...")
                time.sleep(10)

            # Cek apakah form login sudah muncul
            if page.locator("#username").is_visible():
                logging.info("Form login ditemukan. Mengisi kredensial...")
                page.fill("#username", username)
                page.fill("#password", password)
                
                captcha_label = page.locator("label:has-text('Hasil'), label:has-text('Berapa'), label:has-text('dari')")
                if captcha_label.count() > 0:
                    question_text = captcha_label.first.inner_text()
                    logging.info(f"CAPTCHA ditemukan: {question_text}")
                    answer = solve_math(question_text)
                    if answer:
                        logging.info(f"Jawaban CAPTCHA: {answer}")
                        if page.locator("#aritmetika").is_visible():
                            page.fill("#aritmetika", answer)
                        else:
                            page.fill("input[placeholder*='Jawaban']", answer)
                
                logging.info("Mengklik tombol Log in...")
                page.click("button:has-text('Log in')")
                time.sleep(5)
                
                if "login" not in page.url:
                    logging.info(f"Login Berhasil! URL saat ini: {page.url}")
                    page.screenshot(path="success_login.png")
                    check_slots(page)
                else:
                    logging.error("Login Gagal. Masih di halaman login.")
                    page.screenshot(path="login_failed.png")
            else:
                logging.error("Gagal melewati Cloudflare atau form login tidak ditemukan.")
                page.screenshot(path="page_state.png")
                
        except Exception as e:
            logging.error(f"Terjadi kesalahan: {e}")
            page.screenshot(path="error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    # Prioritaskan kredensial yang dicatat di kode, jika tidak ada baru ambil dari env
    USER = ANTAM_USER if ANTAM_USER else os.getenv("ANTAM_USERNAME")
    PASS = ANTAM_PASS if ANTAM_PASS else os.getenv("ANTAM_PASSWORD")
    
    if not USER or not PASS:
        logging.error("Kredensial tidak ditemukan!")
    else:
        run_automation(USER, PASS)
