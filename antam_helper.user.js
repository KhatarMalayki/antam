// ==UserScript==
// @name         Antrean Logam Mulia Helper Pro (v4.4 - Ultra Redirect)
// @namespace    http://tampermonkey.net/
// @version      4.4
// @description  Otomatisasi antrean Antam - Login otomatis super cepat, pemulihan sesi, dan bypass Cloudflare Turnstile (Aggressive Landing Page Auto-Click)
// @author       Manus
// @match        https://antrean.logammulia.com/*
// @match        https://antrean.logammulia.com/
// @grant        GM_notification
// @grant        GM_setValue
// @grant        GM_getValue
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    // --- KONFIGURASI PENGGUNA ---
    const CONFIG = {
        username: '081212149866',
        password: 'nafis2205',
        minRefreshDelay: 10000,
        maxRefreshDelay: 20000,
        enableAutoLogin: true,
        enableCaptchaSolver: true,
        keepAliveInterval: 30000 // Dipercepat ke 30 detik untuk keamanan ekstra
    };

    // --- UTILS ---
    function log(msg) {
        console.log('%c[AntamHelper] ' + msg, 'color: #004aad; font-weight: bold;');
    }

    function getRandomDelay(min, max) {
        return Math.floor(Math.random() * (max - min + 1) + min);
    }

    function notify(title, text) {
        GM_notification({
            title: title,
            text: text,
            timeout: 10000,
            onclick: () => window.focus()
        });
        const audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
        audio.play().catch(() => {});
    }

    // --- LOGIKA CAPTCHA UNIVERSAL ---
    function solveArithmeticUniversal() {
        const elements = Array.from(document.querySelectorAll('label, div, p, h1, h2, h3, h4, h5, span'));
        const targetElement = elements.find(el =>
            (el.innerText.includes('Hasil dari') ||
             el.innerText.includes('hasil perhitungan') ||
             el.innerText.includes('Berapa') ||
             el.innerText.includes('dikurangi') ||
             el.innerText.includes('ditambah')) &&
            /\d+/.test(el.innerText)
        );

        if (targetElement) {
            const text = targetElement.innerText.trim();
            const match = text.match(/(\d+)\s*([\+\-\*\/x]|plus|minus|kali|bagi|ditambah|dikurangi|dikali|dibagi)\s*(\d+)/i);

            if (match) {
                const num1 = parseInt(match[1]);
                const op = match[2].toLowerCase();
                const num2 = parseInt(match[3]);
                let result;

                if (op.includes('tambah') || op === '+' || op === 'plus') result = num1 + num2;
                else if (op.includes('kurang') || op === '-' || op === 'minus' || op.includes('kurangi')) result = num1 - num2;
                else if (op.includes('kali') || op === '*' || op === 'x' || op.includes('dikali')) result = num1 * num2;
                else if (op.includes('bagi') || op === '/' || op.includes('dibagi')) result = Math.floor(num1 / num2);

                if (result !== undefined) {
                    const input = document.getElementById('aritmetika') ||
                                  document.querySelector('input[type="number"]') ||
                                  document.querySelector('input[placeholder*="Jawaban"]');

                    if (input) {
                        input.value = result;
                        ['input', 'change', 'blur', 'keyup'].forEach(evtName => {
                            input.dispatchEvent(new Event(evtName, { bubbles: true }));
                        });
                        log('CAPTCHA BERHASIL DIISI: ' + result);

                        const verifyBtn = Array.from(document.querySelectorAll('button, a')).find(el =>
                            el.innerText.toLowerCase().includes('verify')
                        );
                        if (verifyBtn) {
                            log('Tombol Verify ditemukan, mengklik dalam 1 detik...');
                            setTimeout(() => verifyBtn.click(), 1000);
                        }
                        return true;
                    }
                }
            }
        }
        return false;
    }

    // --- OTOMATISASI PILIH WAKTU ---
    function autoSelectTime() {
        const timeSelect = document.querySelector('select[name="jam"]') ||
                           document.querySelector('select#jam');

        if (timeSelect) {
            const availableOption = Array.from(timeSelect.options).find(opt =>
                opt.text.includes('Tersedia') && !opt.disabled && opt.value !== ""
            );

            if (availableOption) {
                log('Waktu tersedia ditemukan: ' + availableOption.text);
                timeSelect.value = availableOption.value;
                timeSelect.dispatchEvent(new Event('change', { bubbles: true }));

                const submitBtn = document.querySelector('button.btn-primary') ||
                                  Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Ambil Antrean'));

                if (submitBtn && !submitBtn.disabled) {
                    log('Mengklik tombol Ambil Antrean dalam 1.5 detik...');
                    setTimeout(() => submitBtn.click(), 1500);
                }
                return true;
            }
        }
        return false;
    }

    // --- FITUR KEEP ALIVE ---
    function startKeepAlive() {
        setInterval(() => {
            if (document.body.innerText.includes('Logout')) {
                fetch('https://antrean.logammulia.com/users', { cache: 'no-store' }).catch(() => {});
            }
        }, CONFIG.keepAliveInterval);
    }

    // --- HALAMAN LANDING PAGE ---
    function handleLandingPage() {
        log('Landing page terdeteksi. Mengarahkan ke login INSTAN...');
        window.location.replace('https://antrean.logammulia.com/login');
    }

    // --- HALAMAN LOGIN (ULTRA AUTO-LOGIN v4.1) ---
    function handleLoginPage() {
        if (!CONFIG.enableAutoLogin) return;
        log('Halaman login terdeteksi. Memulai Ultra Auto-Login v4.1...');

        const runLogin = () => {
            const userField = document.getElementById('username');
            const passField = document.getElementById('password');
            const loginBtn = document.querySelector('button[type="submit"]');

            if (userField) {
                userField.value = CONFIG.username;
                userField.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (passField) {
                passField.value = CONFIG.password;
                passField.dispatchEvent(new Event('input', { bubbles: true }));
            }

            if (CONFIG.enableCaptchaSolver) {
                // 1. Coba isi CAPTCHA Aritmatika secara agresif
                const captchaInterval = setInterval(() => {
                    const solved = solveArithmeticUniversal();
                    if (solved) {
                        clearInterval(captchaInterval);
                        log('CAPTCHA Aritmatika terisi. Memulai deteksi otomatis Cloudflare Turnstile...');

                        // 2. Cek status Cloudflare Turnstile secara agresif
                        const turnstileCheckInterval = setInterval(() => {
                            const turnstileResponse = document.querySelector('input[name="cf-turnstile-response"]');
                            const turnstileWidget = document.querySelector('.cf-turnstile');

                            // Check if the response token is present (Turnstile solved)
                            if (turnstileResponse && turnstileResponse.value.length > 0) {
                                clearInterval(turnstileCheckInterval);
                                log('Cloudflare Turnstile terdeteksi SUKSES! Melanjutkan login instan...');
                                // Klik tombol login
                                if (loginBtn) {
                                    loginBtn.click();
                                }
                            } else if (!turnstileWidget) {
                                // If no Turnstile widget is present at all, just click login
                                clearInterval(turnstileCheckInterval);
                                log('Tidak ada Cloudflare Turnstile terdeteksi. Melanjutkan login instan...');
                                if (loginBtn) {
                                    loginBtn.click();
                                }
                            } else {
                                log('Menunggu Cloudflare Turnstile selesai...');
                            }
                        }, 500); // Cek setiap 0.5 detik

                        // Timeout untuk Turnstile check (misalnya 15 detik)
                        setTimeout(() => {
                            clearInterval(turnstileCheckInterval);
                            log('Timeout deteksi Turnstile. Mencoba klik login jika tombol tersedia.');
                            if (loginBtn) {
                                loginBtn.click();
                            }
                        }, 15000);

                    } else {
                        log('Menunggu CAPTCHA Aritmatika muncul...');
                    }
                }, 500); // Cek setiap 0.5 detik

                // Timeout jika CAPTCHA tidak muncul-muncul
                setTimeout(() => clearInterval(captchaInterval), 20000);
            }
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', runLogin);
        } else {
            runLogin();
        }
    }

    // --- HALAMAN USERS (AUTO-CLICK MENU ANTREAN) ---
    function handleUsersPage() {
        log('Halaman Users terdeteksi. Mengarahkan ke antrean INSTAN...');
        window.location.replace('https://antrean.logammulia.com/antrean');
    }

    // --- HALAMAN ANTREAN ---
    function handleAntreanPage() {
        const runAntrean = () => {
            const urlParams = new URLSearchParams(window.location.search);
            const currentSite = urlParams.get('site');

            // 1. Cek modal pesan kesalahan
            const modalBody = document.querySelector('.modal-body');
            const modalText = modalBody ? modalBody.innerText : '';
            if (modalText.includes('Mohon maaf') || modalText.includes('belum dibuka') || modalText.includes('tidak tersedia')) {
                log('Pesan sistem terdeteksi: ' + modalText);
                setTimeout(() => location.reload(), 15000);
                return;
            }

            // 2. Cek verifikasi tahap kedua
            const verifyBtn = Array.from(document.querySelectorAll('button, a')).find(el => el.innerText.toLowerCase().includes('verify'));
            if (verifyBtn || document.body.innerText.includes('Berapa')) {
                log('Halaman verifikasi tahap kedua terdeteksi!');
                solveArithmeticUniversal();
                return;
            }

            // 3. Cek dropdown waktu kedatangan
            const timeSelect = document.querySelector('select[name="jam"]') || document.querySelector('select#jam');
            if (timeSelect) {
                log('Dropdown waktu kedatangan terdeteksi!');
                autoSelectTime();
                return;
            }

            if (!currentSite) {
                log('Silakan pilih butik secara manual.');
                return;
            }

            // 4. Monitoring ketersediaan
            const boutiqueName = document.querySelector('.modal-title')?.innerText || 'Butik';
            log(`Memeriksa ketersediaan di ${boutiqueName}...`);

            const bodyText = document.body.innerText;

            // DETEKSI SESI MATI (PENTING)
            if (bodyText.includes('Login') && !bodyText.includes('Logout')) {
                log('SESI MATI! Mengarahkan ke login secepatnya...');
                window.location.replace('https://antrean.logammulia.com/login');
                return;
            }

            const isFull = bodyText.includes('Kuota harian telah terpenuhi') ||
                               bodyText.includes('Pendaftaran ditutup') ||
                               bodyText.includes('Jadwal tidak tersedia');

            const isAvailable = bodyText.includes('Ambil Antrean') ||
                                bodyText.includes('Pilih Jadwal') ||
                                document.querySelector('button.btn-primary:not([disabled])');

            if (isAvailable && !isFull) {
                log('!!! ANTREAN TERSEDIA !!!');
                notify('ANTREAN TERSEDIA!', 'Segera ambil di ' + boutiqueName);

                const ambilBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Ambil Antrean'));
                if (ambilBtn) {
                    log('Klik Ambil Antrean...');
                    ambilBtn.click();
                }

                fetch('https://antrean.logammulia.com/users').catch(() => {});
            } else {
                const delay = getRandomDelay(CONFIG.minRefreshDelay, CONFIG.maxRefreshDelay);
                log(`Kuota penuh/belum buka. Refreshing dalam ${delay/1000} detik...`);
                setTimeout(() => {
                    const currentModal = document.querySelector('.modal-body')?.innerText || '';
                    const currentTimeSelect = document.querySelector('select[name="jam"]');
                    if (!currentModal.includes('Mohon maaf') && !currentTimeSelect) {
                        location.reload();
                    }
                }, delay);
            }
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', runAntrean);
        } else {
            runAntrean();
        }
    }

    // --- ROUTING ENGINE ---
    const init = () => {
        const path = window.location.pathname;
        const url = window.location.href;
        
        log('Routing path: ' + path);

        if (path === '/' || path === '') {
            handleLandingPage();
        } else if (path.includes('/login')) {
            handleLoginPage();
        } else if (path.includes('/antrean')) {
            handleAntreanPage();
        } else if (path.includes('/users') || path.includes('/home')) {
            handleUsersPage();
        } else {
            // Global Session Check
            const checkSession = () => {
                if (document.body && !document.body.innerText.includes('Logout') && !path.includes('/login')) {
                    log('Sesi tidak terdeteksi. Mengarahkan ke login...');
                    window.location.replace('https://antrean.logammulia.com/login');
                }
            };
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', checkSession);
            } else {
                checkSession();
            }
        }
        
        startKeepAlive();
    };

    // Execute immediately
    init();

})();
