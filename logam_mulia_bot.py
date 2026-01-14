import re
import time
import os
import logging
import requests
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

# Kredensial diambil dari .env atau environment variable
ANTAM_USER = os.getenv("ANTAM_USERNAME")
ANTAM_PASS = os.getenv("ANTAM_PASSWORD")

def solve_math(question_text):
    """Menyelesaikan CAPTCHA aritmatika sederhana."""
    logging.info(f"Mencoba menyelesaikan CAPTCHA: {question_text}")
    match = re.search(r'(\d+)\s+(ditambah|dikurangi|dikali|x)\s+(\d+)', question_text.lower())
    if match:
        num1 = int(match.group(1))
        op = match.group(2)
        num3 = int(match.group(3))
        if op == 'ditambah': return str(num1 + num3)
        elif op == 'dikurangi': return str(num1 - num3)
        elif op in ['dikali', 'x']: return str(num1 * num3)
    return None

def send_telegram_msg(message):
    """Mengirim notifikasi ke Telegram."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}
            requests.post(url, json=payload, timeout=10)
            logging.info("Notifikasi Telegram terkirim.")
        except Exception as e:
            logging.error(f"Gagal mengirim notifikasi Telegram: {e}")
    else:
        logging.warning("Token atau Chat ID Telegram tidak ditemukan di .env")

def check_available_slots(page):
    """Mengecek ketersediaan slot antrean."""
    logging.info("Mengecek ketersediaan slot antrean...")
    try:
        # Navigasi ke halaman pengambilan antrean jika belum di sana
        if "ambil-antrean" not in page.url:
            page.goto("https://antrean.logammulia.com/ambil-antrean", wait_until="domcontentloaded")
            time.sleep(5)
        
        # Cari elemen yang menunjukkan slot (ini perlu disesuaikan dengan UI asli)
        # Contoh: mencari teks "Tersedia" atau tombol yang tidak disabled
        slots = page.locator(".slot-item:not(.disabled), button:has-text('Pilih'):not([disabled])")
        count = slots.count()
        
        if count > 0:
            msg = f"🔥 SLOT ANTREAN TERSEDIA! Ditemukan {count} slot aktif."
            logging.info(msg)
            send_telegram_msg(msg)
            page.screenshot(path="slots_available.png")
            return True
        else:
            logging.info("Belum ada slot antrean yang tersedia.")
            return False
    except Exception as e:
        logging.error(f"Gagal mengecek slot: {e}")
        return False

def handle_verification(page):
    """Menangani berbagai jenis verifikasi (Turnstile, reCAPTCHA)."""
    logging.info("Mengecek widget verifikasi...")
    
    # Cek Cloudflare Turnstile
    try:
        turnstile_iframe = page.wait_for_selector("iframe[src*='challenges.cloudflare.com']", timeout=5000)
        if turnstile_iframe:
            logging.info("Widget Turnstile ditemukan.")
            box = turnstile_iframe.bounding_box()
            if box:
                page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                logging.info("Mencoba mengklik widget Turnstile.")
            time.sleep(10)
            return True
    except: pass

    # Cek reCAPTCHA
    try:
        recaptcha_iframe = page.wait_for_selector("iframe[title*='reCAPTCHA']", timeout=5000)
        if recaptcha_iframe:
            logging.info("Widget reCAPTCHA ditemukan. Mencoba klik checkbox...")
            box = recaptcha_iframe.bounding_box()
            if box:
                page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            time.sleep(10)
            return True
    except: pass
    
    return False

def run_automation(username, password):
    with sync_playwright() as p:
        # Gunakan browser chromium dengan beberapa argumen tambahan untuk menghindari deteksi
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ])
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        
        # Apply stealth
        stealth_config = Stealth()
        stealth_config.apply_stealth_sync(page)
        
        try:
            logging.info("Membuka halaman login...")
            page.goto("https://antrean.logammulia.com/login", wait_until="domcontentloaded", timeout=60000)
            
            # Tunggu loading selesai
            time.sleep(5)
            
            # Tangani Verifikasi jika ada
            handle_verification(page)
            
            # Cek apakah form login sudah muncul
            if page.locator("#username").is_visible():
                logging.info("Form login ditemukan. Mengisi kredensial...")
                page.fill("#username", username)
                page.fill("#password", password)
                
                # Tangani CAPTCHA Aritmatika
                captcha_label = page.locator("label:has-text('Hasil'), label:has-text('Berapa'), label:has-text('dari')")
                if captcha_label.count() > 0:
                    question_text = captcha_label.first.inner_text()
                    answer = solve_math(question_text)
                    if answer:
                        logging.info(f"Jawaban CAPTCHA: {answer}")
                        if page.locator("#aritmetika").is_visible():
                            page.fill("#aritmetika", answer)
                        else:
                            # Fallback jika ID berbeda
                            page.locator("input[name*='captcha'], input[placeholder*='Jawaban']").first.fill(answer)
                
                # Simulasi gerakan mouse dan delay acak
                page.mouse.move(100, 100)
                time.sleep(1)
                page.mouse.move(200, 300)
                time.sleep(2)
                
                logging.info("Mengklik tombol Log in...")
                # Gunakan click dengan delay penekanan tombol
                page.click("button:has-text('Log in')", delay=150)
                
                # Tunggu respon setelah klik
                time.sleep(10)
                
                # Cek status login
                current_url = page.url
                if "login" not in current_url:
                    logging.info(f"Login Berhasil! URL saat ini: {current_url}")
                    page.screenshot(path="success_login.png")
                    
                    # Lakukan pengecekan slot setelah login berhasil
                    check_available_slots(page)
                else:
                    logging.error("Login Gagal. Masih di halaman login.")
                    # Cek apakah ada pesan error di halaman
                    error_msg = page.locator(".alert-danger, .text-danger").first.inner_text() if page.locator(".alert-danger, .text-danger").count() > 0 else "Tidak ada pesan error terlihat"
                    logging.error(f"Pesan error di halaman: {error_msg}")
                    page.screenshot(path="login_failed_detail.png")
            else:
                logging.error("Form login tidak ditemukan. Mungkin terblokir Cloudflare.")
                page.screenshot(path="page_state_blocked.png")
                
        except Exception as e:
            logging.error(f"Terjadi kesalahan: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    USER = ANTAM_USER
    PASS = ANTAM_PASS
    
    if not USER or not PASS:
        logging.error("Kredensial tidak ditemukan!")
    else:
        run_automation(USER, PASS)
