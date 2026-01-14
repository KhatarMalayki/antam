import nodriver as uc
import asyncio
import re
import logging
import os
import requests
from dotenv import load_dotenv

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nodriver_bot.log"),
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

async def check_available_slots(page):
    """Mengecek ketersediaan slot antrean menggunakan nodriver."""
    logging.info("Mengecek ketersediaan slot antrean...")
    try:
        if "ambil-antrean" not in page.url:
            await page.get("https://antrean.logammulia.com/ambil-antrean")
            await asyncio.sleep(5)
        
        # Mencari elemen slot
        content = await page.get_content()
        # Logika sederhana: cari teks yang menunjukkan ketersediaan
        if "Pilih" in content and "disabled" not in content.lower():
            msg = "🔥 [Nodriver] SLOT ANTREAN TERSEDIA! Segera cek akun Anda."
            logging.info(msg)
            send_telegram_msg(msg)
            await page.save_screenshot("/home/ubuntu/antam/nodriver_slots_found.png")
            return True
        else:
            logging.info("Belum ada slot antrean yang tersedia.")
            return False
    except Exception as e:
        logging.error(f"Gagal mengecek slot: {e}")
        return False

async def main():
    if not ANTAM_USER or not ANTAM_PASS:
        logging.error("Kredensial tidak ditemukan di .env!")
        return

    logging.info("Memulai browser nodriver...")
    browser = await uc.start(
        no_sandbox=True, 
        headless=True,
        browser_args=[
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "--disable-blink-features=AutomationControlled"
        ]
    )
    
    try:
        logging.info("Membuka halaman login...")
        page = await browser.get("https://antrean.logammulia.com/login")
        
        # Tunggu Cloudflare/reCAPTCHA
        logging.info("Menunggu verifikasi halaman (20 detik)...")
        await asyncio.sleep(20)
        await page.save_screenshot("/home/ubuntu/antam/nodriver_initial.png")
        
        # Cari form login
        try:
            username_input = await page.select("#username", timeout=15)
            if username_input:
                logging.info("Form login ditemukan. Mengisi kredensial...")
                await username_input.send_keys(ANTAM_USER)
                
                password_input = await page.select("#password")
                await password_input.send_keys(ANTAM_PASS)
                
                # Cari label CAPTCHA aritmatika
                try:
                    # Mencoba mencari elemen label yang berisi teks pertanyaan
                    labels = await page.query_selector_all("label")
                    question_text = ""
                    for label in labels:
                        text = label.text
                        if any(word in text.lower() for word in ["hasil dari", "berapa", "ditambah", "dikurangi"]):
                            question_text = text
                            break
                    
                    if not question_text:
                        # Fallback: cari di seluruh konten halaman
                        content = await page.get_content()
                        match = re.search(r'(?:Berapa hasil dari|Hasil dari)\s+([\d\s\w]+)\?', content, re.IGNORECASE)
                        if match:
                            question_text = match.group(1)
                    
                    if question_text:
                        answer = solve_math(question_text)
                        if answer:
                            logging.info(f"Jawaban CAPTCHA: {answer}")
                            captcha_input = await page.select("#aritmetika")
                            if not captcha_input:
                                captcha_input = await page.select("input[name*='captcha']")
                            
                            if captcha_input:
                                await captcha_input.send_keys(answer)
                except Exception as e:
                    logging.warning(f"Gagal memproses CAPTCHA: {e}")
                
                # Klik tombol login
                login_button = await page.select("button[type='submit']")
                if login_button:
                    logging.info("Mengklik tombol Log in...")
                    await login_button.click()
                    
                    # Tunggu hasil login
                    await asyncio.sleep(10)
                    await page.save_screenshot("/home/ubuntu/antam/nodriver_after_login.png")
                    
                    if "login" not in page.url:
                        logging.info(f"Login Berhasil! URL: {page.url}")
                        await check_available_slots(page)
                    else:
                        logging.warning("Gagal login atau masih di halaman login.")
                else:
                    logging.error("Tombol login tidak ditemukan.")
            else:
                logging.error("Form login tidak muncul. Mungkin terblokir verifikasi ketat.")
        except Exception as e:
            logging.error(f"Kesalahan saat interaksi form: {e}")
            await page.save_screenshot("/home/ubuntu/antam/nodriver_error.png")
            
    except Exception as e:
        logging.error(f"Terjadi kesalahan utama: {e}")
    finally:
        logging.info("Menutup browser...")
        # Browser nodriver biasanya ditutup dengan menghentikan loop atau memanggil stop
        # Di versi terbaru, browser.stop() sering digunakan
        try:
            browser.stop()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
