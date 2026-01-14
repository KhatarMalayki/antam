import nodriver as uc
import asyncio
import re
import logging
import os
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

async def main():
    logging.info("Memulai browser nodriver...")
    # Gunakan profil yang lebih realistis
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
        
        # Tunggu Cloudflare Turnstile
        logging.info("Menunggu Cloudflare Turnstile (15 detik)...")
        await asyncio.sleep(15)
        
        await page.save_screenshot("/home/ubuntu/antam/nodriver_initial.png")
        
        # Cek apakah kita masih di halaman login atau terblokir
        content = await page.get_content()
        if "cf-turnstile" in content:
            logging.info("Turnstile terdeteksi. Menunggu validasi otomatis (30 detik)...")
            await asyncio.sleep(30)
            await page.save_screenshot("/home/ubuntu/antam/nodriver_after_wait.png")

        # Cari form login
        try:
            username_input = await page.select("#username", timeout=10)
            if username_input:
                logging.info("Form login ditemukan. Mengisi kredensial...")
                await username_input.send_keys(ANTAM_USER)
                
                password_input = await page.select("#password")
                await password_input.send_keys(ANTAM_PASS)
                
                # Cari label CAPTCHA aritmatika
                labels = await page.query_selector_all("label")
                captcha_text = ""
                for label in labels:
                    text = label.text
                    if any(word in text for word in ["Hasil dari", "ditambah", "dikurangi", "dikali"]):
                        captcha_text = text
                        break
                
                if captcha_text:
                    answer = solve_math(captcha_text)
                    if answer:
                        logging.info(f"Jawaban CAPTCHA: {answer}")
                        captcha_input = await page.select("#aritmetika")
                        if captcha_input:
                            await captcha_input.send_keys(answer)
                
                # Klik tombol login
                login_button = await page.select("button[type='submit']")
                if not login_button:
                    login_button = await page.select("button.btn-primary")
                
                if login_button:
                    logging.info("Mengklik tombol Log in...")
                    await login_button.click()
                    
                    # Tunggu hasil login
                    await asyncio.sleep(10)
                    await page.save_screenshot("/home/ubuntu/antam/nodriver_after_login.png")
                    logging.info(f"URL saat ini: {page.url}")
                    
                    if "login" not in page.url:
                        logging.info("Login sepertinya berhasil!")
                    else:
                        logging.warning("Masih di halaman login. Cek screenshot.")
                else:
                    logging.error("Tombol login tidak ditemukan.")
            else:
                logging.error("Input username tidak ditemukan.")
        except Exception as e:
            logging.error(f"Gagal menemukan elemen form: {e}")
            await page.save_screenshot("/home/ubuntu/antam/nodriver_form_not_found.png")
            
    except Exception as e:
        logging.error(f"Terjadi kesalahan utama: {e}")
    finally:
        # browser.stop() bukan awaitable di versi ini, tapi dipanggil sebagai fungsi biasa
        # atau biarkan saja karena script akan selesai
        pass

if __name__ == "__main__":
    asyncio.run(main())
