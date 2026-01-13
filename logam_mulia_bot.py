import re
import time
import sys
from patchright.sync_api import sync_playwright

def solve_math(question_text):
    match = re.search(r'(\d+)\s+(ditambah|dikurangi|dikali)\s+(\d+)', question_text)
    if match:
        num1 = int(match.group(1))
        op = match.group(2)
        num2 = int(match.group(3))
        if op == 'ditambah': return str(num1 + num2)
        elif op == 'dikurangi': return str(num1 - num2)
        elif op == 'dikali': return str(num1 * num2)
    return None

def run_automation(username, password):
    with sync_playwright() as p:
        # Menggunakan patchright untuk menghindari deteksi bot
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        
        print("Membuka halaman login...")
        page.goto("https://antrean.logammulia.com/login")
        
        # Tunggu sebentar untuk Cloudflare challenge
        time.sleep(10)
        
        # Cek apakah masih ada challenge
        if "challenge" in page.content().lower() or "blocked" in page.content().lower():
            print("Terdeteksi tantangan Cloudflare. Mencoba menunggu...")
            # Terkadang hanya perlu menunggu atau klik manual jika terlihat
            try:
                # Cari iframe turnstile dan klik jika ada
                if page.locator("iframe").count() > 0:
                    print("Mencoba berinteraksi dengan Turnstile...")
                    # Logika klik otomatis Turnstile bisa ditambahkan di sini
            except:
                pass
            time.sleep(10)

        try:
            # Cek apakah form login sudah muncul
            if page.locator("#username").is_visible():
                print("Form login ditemukan.")
                page.fill("#username", username)
                page.fill("#password", password)
                
                captcha_label = page.locator("label:has-text('Hasil'), label:has-text('Berapa')")
                if captcha_label.count() > 0:
                    question_text = captcha_label.first.inner_text()
                    print(f"Pertanyaan: {question_text}")
                    answer = solve_math(question_text)
                    if answer:
                        print(f"Jawaban: {answer}")
                        if page.locator("#aritmetika").is_visible():
                            page.fill("#aritmetika", answer)
                        else:
                            page.fill("input[placeholder='Masukan Jawaban']", answer)
                
                page.click("button:has-text('Log in')")
                time.sleep(5)
                
                if "login" not in page.url:
                    print(f"Login Berhasil! URL: {page.url}")
                    page.screenshot(path="dashboard_v4.png")
                else:
                    print("Login Gagal atau masih di halaman login.")
                    page.screenshot(path="login_failed_v4.png")
            else:
                print("Gagal melewati Cloudflare atau form login tidak ditemukan.")
                page.screenshot(path="cloudflare_blocked_v4.png")
                
        except Exception as e:
            print(f"Kesalahan: {e}")
            page.screenshot(path="error_v4.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_automation("081212149866", "nafis2205")
