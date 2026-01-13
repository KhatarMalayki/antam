import re
import time
from playwright.sync_api import sync_playwright

def solve_math(question_text):
    # Mencari pola angka dan operasi (tambah/kurang/kali)
    # Contoh: "Berapa hasil perhitungan dari 10 ditambah 4 ?" atau "Hasil dari 1 ditambah 9 ?"
    match = re.search(r'(\d+)\s+(ditambah|dikurangi|dikali)\s+(\d+)', question_text)
    if match:
        num1 = int(match.group(1))
        op = match.group(2)
        num2 = int(match.group(3))
        
        if op == 'ditambah':
            return str(num1 + num2)
        elif op == 'dikurangi':
            return str(num1 - num2)
        elif op == 'dikali':
            return str(num1 * num2)
    return None

def run_automation(username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = context.new_page()
        
        print("Membuka halaman login...")
        try:
            page.goto("https://antrean.logammulia.com/login")
            
            # Tunggu form muncul
            page.wait_for_selector("#username")
            
            # Isi Username
            page.fill("#username", username)
            
            # Isi Password
            page.fill("#password", password)
            
            # Ambil teks pertanyaan aritmatika
            # Mencari label yang mengandung kata 'Hasil' atau 'Berapa'
            captcha_label = page.locator("label:has-text('Hasil'), label:has-text('Berapa')")
            question_text = captcha_label.first.inner_text()
            print(f"Pertanyaan: {question_text}")
            
            answer = solve_math(question_text)
            if answer:
                print(f"Jawaban: {answer}")
                # Gunakan ID aritmetika jika ada, atau placeholder
                if page.locator("#aritmetika").is_visible():
                    page.fill("#aritmetika", answer)
                else:
                    page.fill("input[placeholder='Masukan Jawaban']", answer)
            else:
                print("Gagal mendeteksi pertanyaan aritmatika.")
                page.screenshot(path="math_error.png")
                return

            # Klik Login
            page.click("button:has-text('Log in')")
            
            # Tunggu navigasi
            print("Menunggu proses login...")
            time.sleep(5)
            
            if "login" not in page.url:
                print(f"Login Berhasil! URL saat ini: {page.url}")
                page.screenshot(path="dashboard.png")
                print("Screenshot dashboard disimpan.")
            else:
                print("Login Gagal atau masih di halaman login.")
                # Cek apakah ada pesan error
                error_msg = page.locator(".alert-danger").is_visible()
                if error_msg:
                    print(f"Pesan Error: {page.locator('.alert-danger').inner_text()}")
                page.screenshot(path="login_failed.png")

        except Exception as e:
            print(f"Terjadi kesalahan: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_automation("081212149866", "nafis2205")
