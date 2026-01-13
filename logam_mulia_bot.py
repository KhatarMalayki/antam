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

# Kredensial
ANTAM_USER = "081212149866"
ANTAM_PASS = "nafis2205"

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

def handle_cloudflare_turnstile(page):
    """Mencoba menangani widget Cloudflare Turnstile."""
    logging.info("Mengecek widget Cloudflare Turnstile...")
    try:
        # Tunggu iframe Turnstile muncul
        turnstile_iframe = page.wait_for_selector("iframe[src*='challenges.cloudflare.com']", timeout=10000)
        if turnstile_iframe:
            logging.info("Widget Turnstile ditemukan. Menunggu validasi otomatis...")
            # Kadang cukup menunggu, kadang perlu klik di tengah iframe
            # Kita coba tunggu sampai checkbox 'Success' muncul di dalam iframe
            time.sleep(5)
            return True
    except Exception as e:
        logging.info("Widget Turnstile tidak ditemukan atau sudah tervalidasi.")
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
            
            # Tangani Turnstile jika ada
            handle_cloudflare_turnstile(page)
            
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
    USER = ANTAM_USER if ANTAM_USER else os.getenv("ANTAM_USERNAME")
    PASS = ANTAM_PASS if ANTAM_PASS else os.getenv("ANTAM_PASSWORD")
    
    if not USER or not PASS:
        logging.error("Kredensial tidak ditemukan!")
    else:
        run_automation(USER, PASS)
