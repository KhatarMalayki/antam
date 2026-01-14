import re
import os
import time
from dotenv import load_dotenv
from botasaurus.browser import browser, Driver

# Load credentials
load_dotenv()
ANTAM_USER = os.getenv("ANTAM_USERNAME")
ANTAM_PASS = os.getenv("ANTAM_PASSWORD")

def solve_math(question_text):
    """Menyelesaikan CAPTCHA aritmatika sederhana."""
    print(f"Mencoba menyelesaikan CAPTCHA: {question_text}")
    match = re.search(r'(\d+)\s+(ditambah|dikurangi|dikali|x)\s+(\d+)', question_text.lower())
    if match:
        num1 = int(match.group(1))
        op = match.group(2)
        num3 = int(match.group(3))
        if op == 'ditambah': return str(num1 + num3)
        elif op == 'dikurangi': return str(num1 - num3)
        elif op in ['dikali', 'x']: return str(num1 * num3)
    return None

@browser(
    headless=True, # Set to False for local testing
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    block_images=False,
)
def run_antam_bot(driver: Driver, data):
    print("Membuka halaman login Antam menggunakan Botasaurus...")
    driver.google_get("https://antrean.logammulia.com/login")
    
    # Tunggu Cloudflare
    print("Menunggu verifikasi Cloudflare (15 detik)...")
    driver.sleep(15)
    
    # Ambil screenshot awal
    driver.save_screenshot("botasaurus_initial.png")
    
    if driver.is_element_present("#username"):
        print("Form login ditemukan. Mengisi kredensial...")
        
        # Botasaurus secara otomatis menangani pengetikan yang menyerupai manusia
        driver.type("#username", ANTAM_USER)
        driver.sleep(1)
        driver.type("#password", ANTAM_PASS)
        
        # Cek CAPTCHA
        captcha_label = driver.get_element_with_text("Hasil dari", tag="label")
        if not captcha_label:
            captcha_label = driver.get_element_with_text("Berapa", tag="label")
            
        if captcha_label:
            question_text = captcha_label.text
            answer = solve_math(question_text)
            if answer:
                print(f"Jawaban CAPTCHA: {answer}")
                driver.type("#aritmetika", answer)
        
        driver.sleep(2)
        print("Mengklik tombol Log in...")
        driver.click("button[type='submit']")
        
        # Tunggu hasil login
        print("Menunggu respon setelah login...")
        driver.sleep(10)
        
        driver.save_screenshot("botasaurus_result.png")
        
        if "login" not in driver.current_url:
            print(f"Login Berhasil! URL saat ini: {driver.current_url}")
        else:
            print("Login Gagal atau masih di halaman login.")
            # Cek pesan error
            error_el = driver.select(".alert-danger")
            if error_el:
                print(f"Pesan Error: {error_el.text}")
    else:
        print("Form login tidak ditemukan. Mungkin terblokir Cloudflare.")

if __name__ == "__main__":
    if not ANTAM_USER or not ANTAM_PASS:
        print("Kredensial tidak ditemukan di .env!")
    else:
        run_antam_bot()
