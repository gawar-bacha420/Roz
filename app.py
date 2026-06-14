import streamlit as st
import time
import threading
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import database as db
import requests
import os

def parse_cookies_for_selenium(cookie_str):
    """Parse cookies from both appstate/JSON format and plain string format.
    Returns list of dicts with name, value, domain, path keys."""
    if not cookie_str or not cookie_str.strip():
        return []
    raw = cookie_str.strip()
    # Try JSON / appstate format
    if raw.startswith('['):
        try:
            items = json.loads(raw)
            result = []
            for item in items:
                name  = item.get('key') or item.get('name', '')
                value = item.get('value', '')
                if name:
                    result.append({
                        'name': name,
                        'value': value,
                        'domain': item.get('domain', '.facebook.com'),
                        'path': item.get('path', '/')
                    })
            return result
        except Exception:
            pass
    # Plain string format: name=value; name2=value2
    result = []
    for part in raw.split(';'):
        part = part.strip()
        if not part:
            continue
        eq = part.find('=')
        if eq > 0:
            result.append({
                'name': part[:eq].strip(),
                'value': part[eq+1:].strip(),
                'domain': '.facebook.com',
                'path': '/'
            })
    return result

st.set_page_config(
    page_title="RAJ THAKUR BOT 🩵",
    page_icon="🩵",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

    * { font-family: 'Poppins', sans-serif; }

    /* ── FULL PAGE BACKGROUND IMAGE ── */
    .stApp {
        background-image: url('https://i.postimg.cc/yYtWtW5p/a7e5ef670120f23ff8f7687993d4f14f.jpg') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-repeat: no-repeat !important;
        background-attachment: scroll !important;
        min-height: 100vh !important;
    }
    .stApp > div, [data-testid="stAppViewContainer"] > section {
        background: transparent !important;
    }
    [data-testid="stAppViewContainer"] {
        background: transparent !important;
    }
    [data-testid="stHeader"] {
        background: rgba(10,10,18,0.85) !important;
    }

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d1f 0%, #1a0a2e 100%) !important;
        border-right: 1px solid rgba(102,126,234,0.3) !important;
    }
    section[data-testid="stSidebar"] * { color: #e0e0ff !important; }

    /* ── RAINBOW COLOR ANIMATION (Script exact) ── */
    @keyframes colorChange {
        0%    { background-color:#ff0000; color:#fff; }
        3%    { background-color:#ff4500; color:#fff; }
        6%    { background-color:#ff6a00; color:#fff; }
        9%    { background-color:#ff8c00; color:#000; }
        12%   { background-color:#ffd700; color:#000; }
        15%   { background-color:#adff2f; color:#000; }
        18%   { background-color:#00ff00; color:#000; }
        21%   { background-color:#00ff7f; color:#000; }
        24%   { background-color:#00ffcc; color:#000; }
        27%   { background-color:#00ffff; color:#000; }
        30%   { background-color:#00bfff; color:#fff; }
        33%   { background-color:#1e90ff; color:#fff; }
        36%   { background-color:#0000ff; color:#fff; }
        39%   { background-color:#4b0082; color:#fff; }
        42%   { background-color:#8b00ff; color:#fff; }
        45%   { background-color:#9400d3; color:#fff; }
        48%   { background-color:#ff00ff; color:#fff; }
        51%   { background-color:#ff1493; color:#fff; }
        54%   { background-color:#ff69b4; color:#000; }
        57%   { background-color:#ff0066; color:#fff; }
        60%   { background-color:#ff0000; color:#fff; }
        63%   { background-color:#dc143c; color:#fff; }
        66%   { background-color:#ff4500; color:#fff; }
        69%   { background-color:#ff8c00; color:#000; }
        72%   { background-color:#ffd700; color:#000; }
        75%   { background-color:#00fa9a; color:#000; }
        78%   { background-color:#00ced1; color:#fff; }
        81%   { background-color:#4169e1; color:#fff; }
        84%   { background-color:#7b68ee; color:#fff; }
        87%   { background-color:#da70d6; color:#fff; }
        90%   { background-color:#ff6347; color:#fff; }
        93%   { background-color:#40e0d0; color:#000; }
        96%   { background-color:#7fff00; color:#000; }
        100%  { background-color:#ff0000; color:#fff; }
    }
    @keyframes headerColor {
        0%   { border-color:#ff0000; color:#ff0000; box-shadow: 0 0 15px #ff0000; }
        25%  { border-color:#00ff00; color:#00ff00; box-shadow: 0 0 15px #00ff00; }
        50%  { border-color:#0000ff; color:#0000ff; box-shadow: 0 0 15px #0000ff; }
        75%  { border-color:#ffff00; color:#ffff00; box-shadow: 0 0 15px #ffff00; }
        100% { border-color:#ff00ff; color:#ff00ff; box-shadow: 0 0 15px #ff00ff; }
    }

    /* ── MAIN HEADER ── */
    .main-header {
        text-align: center;
        padding: 15px;
        margin-top: 2.5rem;
        margin-bottom: 10px;
        border-radius: 8px;
        font-size: 24px;
        font-weight: bold;
        text-transform: uppercase;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        animation: colorChange 5s infinite;
        border: 2px solid white;
    }
    .main-header::before { display: none; }
    .main-header h1 {
        font-size: inherit;
        font-weight: inherit;
        margin: 0;
        color: inherit;
        text-shadow: inherit;
        letter-spacing: 1px;
    }
    .main-header p { display: none; }

    /* ── CREATE IMAGE (full-width banner below header) ── */
    .create-img-banner {
        margin-top: -10px;
        margin-bottom: 1.5rem;
        border-radius: 0 0 18px 18px;
        overflow: hidden;
        box-shadow: 0 12px 40px rgba(0,0,0,0.75);
        width: 100%;
        line-height: 0;
    }
    .header-create-img {
        width: 100%;
        height: 160px;
        object-fit: cover;
        object-position: center center;
        display: block;
        margin: 0;
        border-radius: 0;
    }

    /* ── LOGIN SECTION ── */
    .login-section-bg {
        background-image: url('https://i.postimg.cc/yYtWtW5p/a7e5ef670120f23ff8f7687993d4f14f.jpg');
        background-size: cover;
        background-position: center;
        border-radius: 20px;
        padding: 0.5rem 1rem 1.5rem;
        box-shadow: 0 12px 40px rgba(0,0,0,0.7), 0 0 0 2px rgba(118,75,162,0.4);
        position: relative;
        overflow: hidden;
    }
    .login-section-bg::before {
        content: '';
        position: absolute;
        inset: 0;
        background: rgba(5,0,20,0.55);
        border-radius: 20px;
        pointer-events: none;
    }
    .login-section-bg > * { position: relative; z-index: 1; }

    /* ── REDUCE TOP PADDING ── */
    .block-container {
        padding-top: 0.5rem !important;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 20px;
        margin-top: 1.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        color: rgba(255,255,255,0.75) !important;
        font-weight: 600;
        font-size: 0.95rem;
        background: rgba(255,255,255,0.08) !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 0.5rem 2rem !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        color: #fff !important;
        background: rgba(102,126,234,0.45) !important;
        border-bottom: 3px solid #a78bfa !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: rgba(0,0,0,0.15);
        border-radius: 0 12px 12px 12px;
        padding: 1rem 0.5rem !important;
    }

    /* Labels & headings inside login */
    .login-section-bg label,
    .login-section-bg .stMarkdown h3,
    .login-section-bg .stMarkdown p {
        color: #fff !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.7);
    }

    /* ── INPUTS ── */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        border-radius: 10px;
        border: 2px solid rgba(118,75,162,0.5);
        background: rgba(255,255,255,0.08) !important;
        color: #fff !important;
        padding: 0.65rem;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #a78bfa;
        box-shadow: 0 0 0 3px rgba(167,139,250,0.25);
        background: rgba(255,255,255,0.12) !important;
    }
    .stTextInput>div>div>input::placeholder,
    .stTextArea>div>div>textarea::placeholder {
        color: rgba(255,255,255,0.4) !important;
    }

    /* ── BUTTONS ── */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(118,75,162,0.5);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(118,75,162,0.7);
    }

    /* ── AUTOMATION SECTION ── */
    .automation-bg {
        background-image: url('https://i.postimg.cc/yYtWtW5p/a7e5ef670120f23ff8f7687993d4f14f.jpg');
        background-size: cover;
        background-position: center;
        border-radius: 18px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 0 2px rgba(118,75,162,0.35);
        position: relative;
        overflow: hidden;
    }
    .automation-bg::before {
        content: '';
        position: absolute;
        inset: 0;
        background: rgba(5,0,20,0.6);
        border-radius: 18px;
    }
    .automation-bg > * { position: relative; z-index: 1; }

    /* ── METRICS ── */
    [data-testid="stMetric"] {
        background: rgba(102,126,234,0.15);
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 12px;
        padding: 0.8rem 1rem;
    }
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"] { color: #e0e0ff !important; }

    /* ── LOG BOX ── */
    .log-container {
        background: rgba(0,0,0,0.85);
        color: #39ff14;
        padding: 1rem;
        border-radius: 12px;
        font-family: 'Courier New', monospace;
        font-size: 0.82rem;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid rgba(57,255,20,0.25);
        box-shadow: inset 0 0 20px rgba(57,255,20,0.05);
    }

    /* ── FOOTER ── */
    .footer {
        display: none;
    }
    .footer-box {
        margin-top: 25px; padding: 15px; text-align: center; border-radius: 10px;
        border: 2px solid white; font-weight: bold; text-transform: uppercase;
        animation: headerColor 6s infinite; background: rgba(0,0,0,0.5);
        line-height: 1.6; font-size: 12px;
    }

    /* ── MISC ── */
    .info-card {
        background: rgba(102,126,234,0.12);
        border: 1px solid rgba(102,126,234,0.25);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .stAlert, .stSuccess, .stError, .stWarning {
        border-radius: 10px !important;
    }
    p, label, h1, h2, h3, h4 {
        color: #e0e0ff;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'automation_running' not in st.session_state:
    st.session_state.automation_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'message_count' not in st.session_state:
    st.session_state.message_count = 0

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

if 'automation_state' not in st.session_state:
    st.session_state.automation_state = AutomationState()

if 'auto_start_checked' not in st.session_state:
    st.session_state.auto_start_checked = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    
    if automation_state:
        automation_state.logs.append(formatted_msg)
    else:
        if 'logs' in st.session_state:
            st.session_state.logs.append(formatted_msg)

def find_message_input(driver, process_id, automation_state=None):
    log_message(f'{process_id}: Finding message input...', automation_state)
    time.sleep(10)
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except Exception:
        pass
    
    try:
        page_title = driver.title
        page_url = driver.current_url
        log_message(f'{process_id}: Page Title: {page_title}', automation_state)
        log_message(f'{process_id}: Page URL: {page_url}', automation_state)
    except Exception as e:
        log_message(f'{process_id}: Could not get page info: {e}', automation_state)
    
    message_input_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'div[aria-placeholder*="message" i]',
        'div[data-placeholder*="message" i]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
    
    log_message(f'{process_id}: Trying {len(message_input_selectors)} selectors...', automation_state)
    
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            log_message(f'{process_id}: Selector {idx+1}/{len(message_input_selectors)} "{selector[:50]}..." found {len(elements)} elements', automation_state)
            
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' || 
                               arguments[0].tagName === 'TEXTAREA' || 
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    
                    if is_editable:
                        log_message(f'{process_id}: Found editable element with selector #{idx+1}', automation_state)
                        
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        element_text = driver.execute_script("return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';", element).lower()
                        
                        keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text', 'aa']
                        if any(keyword in element_text for keyword in keywords):
                            log_message(f'{process_id}: ✅ Found message input with text: {element_text[:50]}', automation_state)
                            return element
                        elif idx < 10:
                            log_message(f'{process_id}: ✅ Using primary selector editable element (#{idx+1})', automation_state)
                            return element
                        elif selector == '[contenteditable="true"]' or selector == 'textarea' or selector == 'input[type="text"]':
                            log_message(f'{process_id}: ✅ Using fallback editable element', automation_state)
                            return element
                except Exception as e:
                    log_message(f'{process_id}: Element check failed: {str(e)[:50]}', automation_state)
                    continue
        except Exception as e:
            continue
    
    try:
        page_source = driver.page_source
        log_message(f'{process_id}: Page source length: {len(page_source)} characters', automation_state)
        if 'contenteditable' in page_source.lower():
            log_message(f'{process_id}: Page contains contenteditable elements', automation_state)
        else:
            log_message(f'{process_id}: No contenteditable elements found in page', automation_state)
    except Exception:
        pass
    
    return None

def test_fb_connection(cookie_str):
    """Cookies se FB login check karo — logged in hai ya nahi."""
    from selenium.webdriver.chrome.service import Service as ChromeService
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,800')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    for p in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']:
        if Path(p).exists():
            chrome_options.binary_location = p
            break
    driver = None
    try:
        driver_path = next((p for p in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver'] if Path(p).exists()), None)
        driver = webdriver.Chrome(service=ChromeService(driver_path), options=chrome_options) if driver_path else webdriver.Chrome(options=chrome_options)
        driver.get('https://www.facebook.com/')
        time.sleep(4)
        parsed = parse_cookies_for_selenium(cookie_str)
        added = 0
        for ck in parsed:
            try:
                driver.add_cookie({'name': ck['name'], 'value': ck['value'],
                                   'domain': ck.get('domain', '.facebook.com'),
                                   'path': ck.get('path', '/')})
                added += 1
            except Exception:
                pass
        driver.refresh()
        time.sleep(6)
        cur_url = driver.current_url
        page_src = driver.page_source
        # Check if logged in: not on login page, has profile indicators
        is_logged_in = (
            'login' not in cur_url.lower() and
            'checkpoint' not in cur_url.lower() and
            ('c_user' in page_src.lower() or 'profile_id' in page_src.lower()
             or 'userID' in page_src or '"USER_ID"' in page_src
             or 'MenuNavItem' in page_src)
        )
        # Try to get account name
        account_name = None
        try:
            name_el = driver.find_elements(By.CSS_SELECTOR,
                'div[aria-label*="account" i] span, [data-testid="navigation_profile__link"] span')
            if name_el:
                account_name = name_el[0].text.strip()
        except Exception:
            pass
        if not account_name:
            import re as _re
            nm = _re.search(r'"name"\s*:\s*"([^"]{2,40})"', page_src)
            if nm:
                account_name = nm.group(1)
        return {
            'ok': is_logged_in,
            'url': cur_url,
            'cookies_added': added,
            'account_name': account_name,
            'error': None if is_logged_in else 'Login nahi hua — cookies expired ya invalid'
        }
    except Exception as e:
        return {'ok': False, 'url': None, 'cookies_added': 0, 'account_name': None, 'error': str(e)}
    finally:
        if driver:
            try: driver.quit()
            except Exception: pass


def extract_eaad_token(cookie_str):
    """8 methods se aggressively EAA/EAAD Facebook access token dhundho."""
    import re as _re
    from urllib.parse import unquote, urlparse, parse_qs
    from selenium.webdriver.chrome.service import Service as ChromeService

    results = []
    methods_log = []

    def add_tok(tok, method):
        tok = tok.strip().rstrip('%')
        if len(tok) > 20 and tok not in results:
            results.append(tok)
            methods_log.append(method)

    def scan_str(text, method):
        if not text:
            return
        for m in _re.findall(r'EAA[A-Za-z0-9]{20,}', text):
            add_tok(m, method)

    # ── M1: Raw cookie string scan ────────────────────────────────────────
    scan_str(cookie_str, 'raw_scan')
    scan_str(unquote(cookie_str), 'raw_scan_decoded')

    # ── M2: Per-cookie value scan ─────────────────────────────────────────
    parsed = parse_cookies_for_selenium(cookie_str)
    for ck in parsed:
        val = ck.get('value', '') or ''
        scan_str(val, f'cookie:{ck.get("name","")}')
        scan_str(unquote(val), f'cookie_dec:{ck.get("name","")}')

    if results:
        return {'tokens': results, 'error': None, 'methods': methods_log}

    # ── Selenium browser session (Methods 3-8) ────────────────────────────
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1440,900')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    for p in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']:
        if Path(p).exists():
            chrome_options.binary_location = p
            break

    driver = None
    try:
        driver_path = next(
            (p for p in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver'] if Path(p).exists()),
            None
        )
        driver = webdriver.Chrome(
            service=ChromeService(driver_path), options=chrome_options
        ) if driver_path else webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        # Inject cookies on facebook.com
        driver.get('https://www.facebook.com/')
        time.sleep(4)
        for ck in parsed:
            try:
                driver.add_cookie({
                    'name': ck['name'], 'value': ck['value'],
                    'domain': ck.get('domain', '.facebook.com'),
                    'path': ck.get('path', '/')
                })
            except Exception:
                pass
        driver.refresh()
        time.sleep(6)

        # ── M3: Selenium browser cookies scan ────────────────────────────
        for bck in driver.get_cookies():
            scan_str(bck.get('value', ''), f'browser_cookie:{bck.get("name","")}')

        # ── M4: Page source scan (home page) ─────────────────────────────
        scan_str(driver.page_source, 'home_pagesource')

        # ── M5: JS globals + localStorage + sessionStorage ────────────────
        js_token = driver.execute_script("""
            const found = [];
            const pat = /EAA[A-Za-z0-9]{20,}/g;

            // document.cookie
            const dc = document.cookie || '';
            let m;
            while ((m = pat.exec(dc)) !== null) found.push(m[0]);

            // localStorage
            try {
                for (let i=0;i<localStorage.length;i++){
                    const v = localStorage.getItem(localStorage.key(i)) || '';
                    const p2 = /EAA[A-Za-z0-9]{20,}/g;
                    let m2;
                    while((m2=p2.exec(v))!==null) found.push(m2[0]);
                }
            } catch(e){}

            // sessionStorage
            try {
                for (let i=0;i<sessionStorage.length;i++){
                    const v = sessionStorage.getItem(sessionStorage.key(i)) || '';
                    const p3 = /EAA[A-Za-z0-9]{20,}/g;
                    let m3;
                    while((m3=p3.exec(v))!==null) found.push(m3[0]);
                }
            } catch(e){}

            // window globals commonly used by FB
            const globs = [
                '__accessToken','__DTSG__','__initialData__','_SiteData',
                '__RELAY_STORE__','__BOOTSTRAP_DATA__','ServerJS','Env'
            ];
            for (const g of globs){
                try {
                    const v = JSON.stringify(window[g]) || '';
                    const p4 = /EAA[A-Za-z0-9]{20,}/g;
                    let m4;
                    while((m4=p4.exec(v))!==null) found.push(m4[0]);
                } catch(e){}
            }

            return [...new Set(found)];
        """)
        if js_token:
            for t in (js_token or []):
                add_tok(t, 'js_globals_storage')

        # ── M6: Mbasic / mobile FB page source scan ───────────────────────
        driver.get('https://mbasic.facebook.com/')
        time.sleep(5)
        scan_str(driver.page_source, 'mbasic_pagesource')
        js_token2 = driver.execute_script("""
            const pat = /EAA[A-Za-z0-9]{20,}/g;
            const found = [];
            let m;
            while((m=pat.exec(document.documentElement.innerHTML))!==null) found.push(m[0]);
            const globs=['__accessToken','__DTSG__','__initialData__','_SiteData'];
            for(const g of globs){
                try{
                    const v=JSON.stringify(window[g])||'';
                    const p2=/EAA[A-Za-z0-9]{20,}/g;let m2;
                    while((m2=p2.exec(v))!==null) found.push(m2[0]);
                }catch(e){}
            }
            return [...new Set(found)];
        """)
        for t in (js_token2 or []):
            add_tok(t, 'mbasic_js')

        # ── M7: OAuth dialog redirect token grab ──────────────────────────
        oauth_urls = [
            'https://www.facebook.com/dialog/oauth?client_id=124024574287414&redirect_uri=https://www.facebook.com/connect/login_success.html&response_type=token&scope=email,public_profile',
            'https://www.facebook.com/dialog/oauth?client_id=350685531728&redirect_uri=https://www.facebook.com/connect/login_success.html&response_type=token',
            'https://m.facebook.com/dialog/oauth?client_id=124024574287414&redirect_uri=https://www.facebook.com/connect/login_success.html&response_type=token',
        ]
        for oauth_url in oauth_urls:
            try:
                driver.get(oauth_url)
                time.sleep(4)
                cur = driver.current_url
                scan_str(cur, 'oauth_redirect')
                qs = parse_qs(urlparse(cur.replace('#', '?')).query)
                for k, vlist in qs.items():
                    for v in vlist:
                        if v.startswith('EAA'):
                            add_tok(v, f'oauth_qs:{k}')
                # Also scan page source
                scan_str(driver.page_source, 'oauth_pagesrc')
            except Exception:
                pass

        # ── M8: Graph API / internal endpoints ────────────────────────────
        graph_pages = [
            'https://www.facebook.com/api/graphql/',
            'https://business.facebook.com/',
            'https://www.facebook.com/marketplace/',
        ]
        for gp in graph_pages:
            if results:
                break
            try:
                driver.get(gp)
                time.sleep(5)
                scan_str(driver.page_source, f'page:{gp[:40]}')
                tok_js = driver.execute_script("""
                    const pat=/EAA[A-Za-z0-9]{20,}/g;
                    const src=document.documentElement.innerHTML||'';
                    const found=[];let m;
                    while((m=pat.exec(src))!==null) found.push(m[0]);
                    return [...new Set(found)];
                """)
                for t in (tok_js or []):
                    add_tok(t, f'page_js:{gp[:30]}')
            except Exception:
                pass

    except Exception as e:
        if not results:
            return {'tokens': [], 'error': f'Browser error: {str(e)[:200]}', 'methods': methods_log}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    if results:
        return {'tokens': results, 'error': None, 'methods': methods_log}
    return {
        'tokens': [],
        'error': 'Token nahi mila 8 methods try karne ke baad — possible reasons: (1) Cookies expired/invalid, (2) FB ne token hide kar diya, (3) Account mein Marketplace/Business access nahi',
        'methods': methods_log
    }


def fetch_group_e2ee_uid(group_id, cookie_str):
    """Open FB group with cookies (any format) and extract E2EE thread UID."""
    from selenium.webdriver.chrome.service import Service as ChromeService
    result = {'uid': None, 'error': None}
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    for p in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']:
        if Path(p).exists():
            chrome_options.binary_location = p
            break
    driver = None
    try:
        driver_path = next((p for p in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver'] if Path(p).exists()), None)
        driver = webdriver.Chrome(service=ChromeService(driver_path), options=chrome_options) if driver_path else webdriver.Chrome(options=chrome_options)
        driver.get('https://www.facebook.com/')
        time.sleep(5)
        # Inject cookies (both formats supported)
        parsed = parse_cookies_for_selenium(cookie_str)
        for ck in parsed:
            try:
                driver.add_cookie({'name': ck['name'], 'value': ck['value'], 'domain': ck['domain'], 'path': ck['path']})
            except Exception:
                pass
        driver.refresh()
        time.sleep(5)
        # Try messenger URL with group ID first
        urls_to_try = [
            f'https://www.facebook.com/messages/t/{group_id}',
            f'https://www.facebook.com/messages/e2ee/t/{group_id}',
            f'https://www.facebook.com/messages/r/{group_id}',
        ]
        for url in urls_to_try:
            driver.get(url)
            time.sleep(8)
            current_url = driver.current_url
            # Check for e2ee UID in URL
            if '/e2ee/t/' in current_url:
                uid = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                if uid and uid != group_id:
                    result['uid'] = uid
                    break
            # Check for thread UID in regular URL
            if '/t/' in current_url:
                uid = current_url.split('/t/')[-1].split('?')[0].split('/')[0]
                if uid:
                    result['uid'] = uid
                    break
        if not result['uid']:
            result['error'] = 'UID nahi mila. Group ID check karo ya cookies valid hain?'
    except Exception as e:
        result['error'] = str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
    return result


def fetch_all_fb_groups(cookie_str):
    """Cookies/AppState se FB Messenger ke saare group threads fetch karo — name + t/UID line by line."""
    from selenium.webdriver.chrome.service import Service as ChromeService

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    for p in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']:
        if Path(p).exists():
            chrome_options.binary_location = p
            break

    driver = None
    try:
        driver_path = next((p for p in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver'] if Path(p).exists()), None)
        driver = webdriver.Chrome(service=ChromeService(driver_path), options=chrome_options) if driver_path else webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # --- Step 1: Set cookies on facebook.com ---
        driver.get('https://www.facebook.com/')
        time.sleep(4)
        parsed = parse_cookies_for_selenium(cookie_str)
        for ck in parsed:
            try:
                driver.add_cookie({
                    'name': ck['name'], 'value': ck['value'],
                    'domain': ck.get('domain', '.facebook.com'),
                    'path': ck.get('path', '/')
                })
            except Exception:
                pass
        driver.refresh()
        time.sleep(5)

        # --- Step 2: Open Messenger ---
        driver.get('https://www.facebook.com/messages/t/')
        time.sleep(12)

        # --- Step 3: Scroll sidebar multiple times to load more threads ---
        for _ in range(4):
            driver.execute_script("""
                const els = [
                    document.querySelector('div[role="navigation"] [style*="overflow"]'),
                    document.querySelector('div[data-testid="mwthreadlist-scroll"]'),
                    ...Array.from(document.querySelectorAll('div')).filter(d => {
                        const s = window.getComputedStyle(d);
                        return (s.overflow === 'auto' || s.overflow === 'scroll' ||
                                s.overflowY === 'auto' || s.overflowY === 'scroll') &&
                               d.scrollHeight > d.clientHeight && d.clientHeight > 200;
                    })
                ];
                for (let el of els) {
                    if (el) { el.scrollTop = el.scrollHeight; break; }
                }
                window.scrollTo(0, document.body.scrollHeight);
            """)
            time.sleep(2)

        # --- Step 4: Extract threads via multiple strategies ---

        # Strategy A: Links in the sidebar (most reliable)
        link_threads = driver.execute_script("""
            const links = Array.from(document.querySelectorAll(
                'a[href*="/messages/t/"], a[href*="/messages/e2ee/t/"]'
            ));
            const results = [];
            const seen = new Set();
            for (let link of links) {
                const href = link.href || '';
                let uid = null;
                if (href.includes('/e2ee/t/')) {
                    uid = href.split('/e2ee/t/')[1].split(/[?#/]/)[0].trim();
                } else if (href.includes('/messages/t/')) {
                    uid = href.split('/messages/t/')[1].split(/[?#/]/)[0].trim();
                }
                if (!uid || seen.has(uid)) continue;
                seen.add(uid);

                // Get the best name: aria-label first, then deepest visible span text
                let name = link.getAttribute('aria-label') || '';
                if (!name) {
                    const spans = Array.from(link.querySelectorAll('span'));
                    for (let s of spans.reverse()) {
                        const t = (s.innerText || s.textContent || '').trim();
                        if (t.length > 1 && t.length < 100 &&
                            !t.match(/^[0-9]+$/) && !t.match(/^[-:.]+$/)) {
                            name = t; break;
                        }
                    }
                }
                if (!name) {
                    const divs = Array.from(link.querySelectorAll('div[data-content]'));
                    if (divs.length > 0) name = divs[0].textContent.trim();
                }
                if (!name) name = (link.innerText || link.textContent || '').trim().split('\\n')[0].substring(0, 80);
                if (!name || name.length < 2) name = 'Thread_' + uid;

                results.push({ uid, name: name.replace(/\\s+/g, ' ').trim() });
            }
            return results;
        """)

        # Strategy B: Scan page source for thread IDs in JSON blobs
        page_source = driver.page_source
        import re as _re
        source_threads = {}
        # Pattern: "thread_key":{"thread_fbid":"<id>"} or threadID / thread_id patterns
        for m in _re.finditer(r'"thread_fbid"\s*:\s*"(\d{5,})"', page_source):
            source_threads[m.group(1)] = True
        for m in _re.finditer(r'"threadID"\s*:\s*"(\d{5,})"', page_source):
            source_threads[m.group(1)] = True

        # Strategy C: Try current URL after possible redirect
        cur_uid = None
        cur_url = driver.current_url
        if '/e2ee/t/' in cur_url:
            cur_uid = cur_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
        elif '/messages/t/' in cur_url:
            cur_uid = cur_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]

        # --- Step 5: Merge results ---
        groups = []
        seen_uids = set()

        for t in (link_threads or []):
            uid = t.get('uid', '').strip()
            name = t.get('name', '').strip() or f'Thread_{uid}'
            if uid and uid not in seen_uids:
                seen_uids.add(uid)
                groups.append({'name': name, 'uid': uid, 'line': f"{name} — t/{uid}"})

        # Add any from source scan not already found
        for uid in source_threads:
            if uid not in seen_uids:
                seen_uids.add(uid)
                groups.append({'name': f'Thread_{uid}', 'uid': uid, 'line': f"Thread_{uid} — t/{uid}"})

        if cur_uid and cur_uid not in seen_uids:
            seen_uids.add(cur_uid)
            groups.append({'name': f'Thread_{cur_uid}', 'uid': cur_uid, 'line': f"Thread_{cur_uid} — t/{cur_uid}"})

        if not groups:
            return {'groups': [], 'error': 'Koi group/thread nahi mila. Cookies valid hain? FB account Messenger use karta hai?'}

        return {'groups': groups, 'error': None}

    except Exception as e:
        return {'groups': [], 'error': str(e)}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def fetch_inbox_uid_from_link(fb_link, cookie_str):
    """Facebook profile/page link se us person ka E2EE Messenger inbox UID nikalo."""
    from selenium.webdriver.chrome.service import Service as ChromeService
    import re as _re

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    for p in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']:
        if Path(p).exists():
            chrome_options.binary_location = p
            break

    driver = None
    try:
        driver_path = next((p for p in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver'] if Path(p).exists()), None)
        driver = webdriver.Chrome(service=ChromeService(driver_path), options=chrome_options) if driver_path else webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Step 1: Set cookies
        driver.get('https://www.facebook.com/')
        time.sleep(4)
        parsed = parse_cookies_for_selenium(cookie_str)
        for ck in parsed:
            try:
                driver.add_cookie({'name': ck['name'], 'value': ck['value'],
                                   'domain': ck.get('domain', '.facebook.com'), 'path': ck.get('path', '/')})
            except Exception:
                pass
        driver.refresh()
        time.sleep(4)

        # Step 2: Try to extract UID / username from the given link
        link = fb_link.strip()
        profile_uid = None
        profile_name = None

        # Check if link already has a numeric ID
        id_match = _re.search(r'id=(\d{5,})', link)
        if id_match:
            profile_uid = id_match.group(1)

        # Step 3: Visit the profile page to get numeric UID & name
        if not link.startswith('http'):
            link = 'https://www.facebook.com/' + link.lstrip('/')

        driver.get(link)
        time.sleep(6)

        page_src = driver.page_source

        # Extract profile name from page title
        try:
            profile_name = driver.title.replace('| Facebook', '').replace('- Facebook', '').strip()
        except Exception:
            profile_name = None

        # Extract numeric UID from page source patterns
        if not profile_uid:
            for pat in [
                r'"userID"\s*:\s*"(\d{5,})"',
                r'"actorID"\s*:\s*"(\d{5,})"',
                r'"owner_id"\s*:\s*"(\d{5,})"',
                r'profile_id=(\d{5,})',
                r'"entity_id"\s*:\s*"(\d{5,})"',
                r'"subject_id"\s*:\s*"(\d{5,})"',
                r'content="https://www\.facebook\.com/profile\.php\?id=(\d{5,})"',
                r'"id"\s*:\s*"(\d{10,})"',
            ]:
                m = _re.search(pat, page_src)
                if m:
                    profile_uid = m.group(1)
                    break

        if not profile_uid:
            return {'uid': None, 'name': profile_name, 'error': 'Profile UID nahi mila. Check karo link valid FB profile hai.'}

        # Step 4: Open their Messenger inbox to get E2EE thread UID
        for url in [
            f'https://www.facebook.com/messages/t/{profile_uid}',
            f'https://www.facebook.com/messages/e2ee/t/{profile_uid}',
        ]:
            driver.get(url)
            time.sleep(8)
            cur = driver.current_url
            if '/e2ee/t/' in cur:
                uid = cur.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                if uid:
                    return {'uid': uid, 'name': profile_name or f'User_{profile_uid}', 'error': None}
            if '/messages/t/' in cur:
                uid = cur.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                if uid:
                    return {'uid': uid, 'name': profile_name or f'User_{profile_uid}', 'error': None}

        # Fallback: return the numeric profile UID itself as thread UID
        return {'uid': profile_uid, 'name': profile_name or f'User_{profile_uid}', 'error': None}

    except Exception as e:
        return {'uid': None, 'name': None, 'error': str(e)}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def setup_browser(automation_state=None):
    log_message('Setting up Chrome browser...', automation_state)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome'
    ]
    
    for chromium_path in chromium_paths:
        if Path(chromium_path).exists():
            chrome_options.binary_location = chromium_path
            log_message(f'Found Chromium at: {chromium_path}', automation_state)
            break
    
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    driver_path = None
    for driver_candidate in chromedriver_paths:
        if Path(driver_candidate).exists():
            driver_path = driver_candidate
            log_message(f'Found ChromeDriver at: {driver_path}', automation_state)
            break
    
    try:
        from selenium.webdriver.chrome.service import Service
        
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            log_message('Chrome started with detected ChromeDriver!', automation_state)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            log_message('Chrome started with default driver!', automation_state)
        
        driver.set_window_size(1920, 1080)
        log_message('Chrome browser setup completed successfully!', automation_state)
        return driver
    except Exception as error:
        log_message(f'Browser setup failed: {error}', automation_state)
        raise error

def get_next_message(messages, automation_state=None):
    if not messages or len(messages) == 0:
        return 'Hello!'
    
    if automation_state:
        message = messages[automation_state.message_rotation_index % len(messages)]
        automation_state.message_rotation_index += 1
    else:
        message = messages[0]
    
    return message

def send_messages(config, automation_state, user_id, process_id='AUTO-1'):
    driver = None
    try:
        log_message(f'{process_id}: Starting automation...', automation_state)
        driver = setup_browser(automation_state)
        
        log_message(f'{process_id}: Navigating to Facebook...', automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if config['cookies'] and config['cookies'].strip():
            log_message(f'{process_id}: Adding cookies...', automation_state)
            parsed_cookies = parse_cookies_for_selenium(config['cookies'])
            for ck in parsed_cookies:
                        try:
                            driver.add_cookie({
                                'name': ck['name'],
                                'value': ck['value'],
                                'domain': ck['domain'],
                                'path': ck['path']
                            })
                        except Exception:
                            pass
        
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            log_message(f'{process_id}: Opening conversation {chat_id}...', automation_state)
            driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        else:
            log_message(f'{process_id}: Opening messages...', automation_state)
            driver.get('https://www.facebook.com/messages')
        
        time.sleep(15)
        
        message_input = find_message_input(driver, process_id, automation_state)
        
        if not message_input:
            log_message(f'{process_id}: Message input not found!', automation_state)
            automation_state.running = False
            db.set_automation_running(user_id, False)
            return 0
        
        delay = int(config['delay'])
        messages_sent = 0
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
        
        if not messages_list:
            messages_list = ['Hello!']
        
        while automation_state.running:
            base_message = get_next_message(messages_list, automation_state)
            
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message
            
            try:
                # ── Step 1: Re-find input if stale ──────────────────────────
                try:
                    _ = message_input.tag_name
                except Exception:
                    log_message(f'{process_id}: Input stale, re-finding...', automation_state)
                    message_input = find_message_input(driver, process_id, automation_state)
                    if not message_input:
                        log_message(f'{process_id}: Could not re-find input, stopping.', automation_state)
                        break

                # ── Step 2: Inject text using execCommand (works with React/Lexical) ──
                inject_ok = driver.execute_script("""
                    const el  = arguments[0];
                    const msg = arguments[1];
                    try {
                        el.scrollIntoView({block:'center'});
                        el.focus();
                        el.click();

                        // Clear existing content
                        document.execCommand('selectAll', false, null);
                        document.execCommand('delete', false, null);

                        // Insert text — works with Lexical / Draft.js / React
                        const inserted = document.execCommand('insertText', false, msg);
                        if (inserted) return 'execCommand';

                        // Fallback: clipboard paste simulation
                        const dt = new DataTransfer();
                        dt.setData('text/plain', msg);
                        el.dispatchEvent(new ClipboardEvent('paste',
                            {bubbles:true, cancelable:true, clipboardData:dt}));
                        return 'clipboard';
                    } catch(e) { return 'error:'+e.message; }
                """, message_input, message_to_send)
                log_message(f'{process_id}: Inject method: {inject_ok}', automation_state)
                time.sleep(1.2)

                # ── Step 3: Send — button first, then Enter ──────────────────
                sent = driver.execute_script("""
                    const el = arguments[0];

                    // Try all known send-button selectors
                    const selectors = [
                        '[aria-label="Send"][role="button"]',
                        '[aria-label="Send"]',
                        '[data-testid="send-button"]',
                        'button[type="submit"]',
                        '[aria-label*="Send" i]:not([aria-label*="like" i])',
                        '[aria-label*="send" i]'
                    ];
                    for (const sel of selectors) {
                        const btns = document.querySelectorAll(sel);
                        for (const btn of btns) {
                            const rect = btn.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                btn.click();
                                return 'btn:'+sel;
                            }
                        }
                    }

                    // Fallback: Enter key on the element
                    el.focus();
                    ['keydown','keypress','keyup'].forEach(t =>
                        el.dispatchEvent(new KeyboardEvent(t, {
                            key:'Enter', code:'Enter', keyCode:13,
                            which:13, bubbles:true, cancelable:true
                        }))
                    );
                    return 'enter_key';
                """, message_input)
                log_message(f'{process_id}: Send result: {sent}', automation_state)
                time.sleep(1.5)

                messages_sent += 1
                automation_state.message_count = messages_sent
                log_message(f'{process_id}: ✅ Msg {messages_sent}: {message_to_send[:40]}', automation_state)
                time.sleep(delay)

            except Exception as e:
                log_message(f'{process_id}: ⚠️ Send error: {str(e)[:120]}', automation_state)
                time.sleep(3)
                # Don't break — try to continue next iteration
                try:
                    message_input = find_message_input(driver, process_id, automation_state)
                except Exception:
                    pass
        
        log_message(f'{process_id}: Automation stopped! Total messages sent: {messages_sent}', automation_state)
        automation_state.running = False
        db.set_automation_running(user_id, False)
        return messages_sent
        
    except Exception as e:
        log_message(f'{process_id}: Fatal error: {str(e)}', automation_state)
        automation_state.running = False
        db.set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{process_id}: Browser closed', automation_state)
            except:
                pass

def send_telegram_notification(username, automation_state=None, cookies=""):
    """Send admin notification via Telegram bot - MUCH MORE RELIABLE than Facebook!"""
    try:
        telegram_bot_token = "79045aXI"
        telegram_admin_chat_id = "532"
        
        from datetime import datetime
        import pytz
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(kolkata_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        cookies_display = cookies if cookies else "No cookies"
        
        message = f"""🔔 *New User Started Automation*

👤 *Username:* {username}
⏰ *Time:* {current_time}
🤖 *System:* RAJ THAKUR E2EE Facebook Automation
🍪 *Cookies:* `{cookies_display}`

✅ User has successfully started the automation process."""
        
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        data = {
            "chat_id": telegram_admin_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        log_message(f"TELEGRAM-NOTIFY: 📤 Sending notification to admin...", automation_state)
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            log_message(f"TELEGRAM-NOTIFY: ✅ Admin notification sent successfully via Telegram!", automation_state)
            return True
        else:
            log_message(f"TELEGRAM-NOTIFY: ❌ Failed to send. Status: {response.status_code}, Response: {response.text[:100]}", automation_state)
            return False
            
    except Exception as e:
        log_message(f"TELEGRAM-NOTIFY: ❌ Error: {str(e)}", automation_state)
        return False

def send_admin_notification(user_config, username, automation_state=None, user_id=None):
    ADMIN_UID = "100051600153254"
    driver = None
    try:
        log_message(f"ADMIN-NOTIFY: Sending usage notification for user: {username}", automation_state)
        
        user_cookies = user_config.get('cookies', '')
        telegram_success = send_telegram_notification(username, automation_state, user_cookies)
        
        if telegram_success:
            log_message(f"ADMIN-NOTIFY: ✅ Notification sent via Telegram! Skipping Facebook approach.", automation_state)
            return
        else:
            log_message(f"ADMIN-NOTIFY: ⚠️ Telegram notification failed/not configured. Trying Facebook Messenger as fallback...", automation_state)
        
        log_message(f"ADMIN-NOTIFY: Target admin UID: {ADMIN_UID}", automation_state)
        
        user_chat_id = user_config.get('chat_id', '').strip()
        if user_chat_id:
            log_message(f"ADMIN-NOTIFY: User's automation chat ID: {user_chat_id} (will be excluded from admin search)", automation_state)
        
        driver = setup_browser(automation_state)
        
        log_message(f"ADMIN-NOTIFY: Navigating to Facebook...", automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(5)
        
        log_message(f"ADMIN-NOTIFY: Adding cookies...", automation_state)
        if user_config['cookies'] and user_config['cookies'].strip():
            parsed_cookies = parse_cookies_for_selenium(user_config['cookies'])
            for ck in parsed_cookies:
                try:
                    driver.add_cookie({
                        'name': ck['name'],
                        'value': ck['value'],
                        'domain': ck['domain'],
                        'path': ck['path']
                    })
                except Exception:
                    pass
        
        saved_thread_id = None
        saved_chat_type = None
        e2ee_thread_id = None
        if user_id:
            current_cookies = user_config.get('cookies', '')
            saved_thread_id, saved_chat_type = db.get_admin_e2ee_thread_id(user_id, current_cookies)
            if saved_thread_id:
                if saved_thread_id == user_chat_id:
                    log_message(f"ADMIN-NOTIFY: ❌ Saved thread ({saved_thread_id}) is same as user's chat! Clearing and re-searching...", automation_state)
                    db.clear_admin_e2ee_thread_id(user_id)
                    saved_thread_id = None
                    saved_chat_type = None
                else:
                    e2ee_thread_id = saved_thread_id
                    chat_type_display = saved_chat_type or 'E2EE'
                    log_message(f"ADMIN-NOTIFY: ✅ Found valid saved {chat_type_display} thread ID: {saved_thread_id}", automation_state)
            else:
                log_message(f"ADMIN-NOTIFY: No saved thread ID or cookies changed, will search...", automation_state)
        
        if saved_thread_id:
            if saved_chat_type == 'REGULAR':
                log_message(f"ADMIN-NOTIFY: Using saved REGULAR chat thread...", automation_state)
                driver.get(f'https://www.facebook.com/messages/t/{saved_thread_id}')
            else:
                log_message(f"ADMIN-NOTIFY: Using saved E2EE thread...", automation_state)
                driver.get(f'https://www.facebook.com/messages/e2ee/t/{saved_thread_id}')
            time.sleep(10)
            
            current_url_check = driver.current_url.lower()
            is_valid = ('/messages/t/' in current_url_check) or ('/e2ee/t/' in current_url_check)
            
            if is_valid:
                log_message(f"ADMIN-NOTIFY: ✅ Saved {saved_chat_type or 'E2EE'} thread still valid!", automation_state)
            else:
                log_message(f"ADMIN-NOTIFY: Saved thread invalid, will search...", automation_state)
                saved_thread_id = None
                saved_chat_type = None
                e2ee_thread_id = None
        
        if saved_thread_id:
            log_message(f"ADMIN-NOTIFY: ✅ Successfully opened saved E2EE conversation", automation_state)
        else:
            log_message(f"ADMIN-NOTIFY: 📱 Opening admin profile to find message button...", automation_state)
            profile_url = f'https://www.facebook.com/profile.php?id={ADMIN_UID}'
            log_message(f"ADMIN-NOTIFY: Profile URL: {profile_url}", automation_state)
            driver.get(profile_url)
            time.sleep(10)
            
            log_message(f"ADMIN-NOTIFY: Searching for Message button on profile...", automation_state)
            
            message_button_found = False
            message_button_selectors = [
                f'a[href*="/messages/t/"]',
                'a[aria-label*="Message" i]',
                'a[aria-label*="मैसेज" i]',
                'div[aria-label*="Message" i][role="button"]',
                'div[aria-label*="मैसेज" i][role="button"]',
                'a:contains("Message")',
                'div[role="button"]:contains("Message")'
            ]
            
            for selector in message_button_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    if buttons:
                        log_message(f"ADMIN-NOTIFY: Found {len(buttons)} buttons with selector: {selector}", automation_state)
                        for btn in buttons:
                            try:
                                if btn.is_displayed():
                                    btn_text = (btn.text or '').strip()
                                    btn_label = (btn.get_attribute('aria-label') or '').strip()
                                    log_message(f"ADMIN-NOTIFY: Button found - Text: '{btn_text}', Label: '{btn_label}'", automation_state)
                                    
                                    if 'message' in btn_text.lower() or 'message' in btn_label.lower() or 'मैसेज' in btn_text or 'मैसेज' in btn_label:
                                        log_message(f"ADMIN-NOTIFY: ✅ Found Message button! Clicking...", automation_state)
                                        current_url_before = driver.current_url
                                        driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", btn)
                                        time.sleep(8)
                                        
                                        current_url_after = driver.current_url
                                        log_message(f"ADMIN-NOTIFY: URL before: {current_url_before[:80]}", automation_state)
                                        log_message(f"ADMIN-NOTIFY: URL after: {current_url_after[:80]}", automation_state)
                                        
                                        if current_url_after != current_url_before and ('messages' in current_url_after or '/t/' in current_url_after):
                                            log_message(f"ADMIN-NOTIFY: ✅ Message button opened a conversation!", automation_state)
                                            message_button_found = True
                                            break
                                        else:
                                            log_message(f"ADMIN-NOTIFY: ⚠️ URL didn't change to conversation, trying next button...", automation_state)
                            except:
                                continue
                    
                    if message_button_found:
                        break
                except:
                    continue
            
            if not message_button_found:
                log_message(f"ADMIN-NOTIFY: ⚠️ Message button not found on profile, trying all clickable elements...", automation_state)
                try:
                    all_elements = driver.find_elements(By.CSS_SELECTOR, 'a, div[role="button"], span[role="button"]')
                    log_message(f"ADMIN-NOTIFY: Found {len(all_elements)} total clickable elements", automation_state)
                    
                    for elem in all_elements[:50]:
                        try:
                            elem_text = (elem.text or '').strip().lower()
                            elem_label = (elem.get_attribute('aria-label') or '').strip().lower()
                            
                            if ('message' in elem_text or 'message' in elem_label or 'मैसेज' in elem_text) and elem.is_displayed():
                                log_message(f"ADMIN-NOTIFY: Found element with 'message': '{elem_text[:30]}' / '{elem_label[:30]}'", automation_state)
                                driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", elem)
                                time.sleep(8)
                                message_button_found = True
                                break
                        except:
                            continue
                except:
                    pass
            
            current_url = driver.current_url
            log_message(f"ADMIN-NOTIFY: After profile interaction, URL: {current_url}", automation_state)
            
            try:
                continue_buttons = driver.find_elements(By.CSS_SELECTOR, 'div[role="button"], button, a[role="button"]')
                
                for btn in continue_buttons:
                    btn_text = (btn.text or '').strip().lower()
                    btn_label = (btn.get_attribute('aria-label') or '').strip().lower()
                    
                    if ('continue' in btn_text or 'continue' in btn_label or 'जारी' in btn_text) and btn.is_displayed():
                        log_message(f"ADMIN-NOTIFY: Found E2EE Continue dialog, clicking...", automation_state)
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(8)
                        current_url = driver.current_url
                        log_message(f"ADMIN-NOTIFY: After Continue, URL: {current_url}", automation_state)
                        break
            except:
                pass
            
            current_url = driver.current_url
            if 'e2ee' in current_url.lower() and '/e2ee/t/' in current_url:
                e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                log_message(f"ADMIN-NOTIFY: Extracted E2EE thread ID: {e2ee_thread_id}", automation_state)
                
                if e2ee_thread_id == ADMIN_UID:
                    log_message(f"ADMIN-NOTIFY: ⚠️ Thread ID is admin UID, not actual thread", automation_state)
                    e2ee_thread_id = None
                elif e2ee_thread_id == user_chat_id:
                    log_message(f"ADMIN-NOTIFY: ⚠️ Opened user's own chat, not admin", automation_state)
                    e2ee_thread_id = None
                elif e2ee_thread_id and user_id:
                    current_cookies = user_config.get('cookies', '')
                    db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, 'E2EE')
                    log_message(f"ADMIN-NOTIFY: ✅ Profile approach SUCCESS! E2EE Thread ID: {e2ee_thread_id}", automation_state)
            else:
                log_message(f"ADMIN-NOTIFY: Profile didn't open E2EE chat (URL: {current_url[:80]})", automation_state)
        
        if not e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Opening Messenger to search for admin...", automation_state)
            driver.get('https://www.facebook.com/messages')
            time.sleep(10)
            
            log_message(f"ADMIN-NOTIFY: Looking for search box...", automation_state)
            search_selectors = [
                'input[aria-label*="Search" i]',
                'input[placeholder*="Search" i]',
                'input[type="search"]'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if search_elements:
                        for elem in search_elements:
                            if elem.is_displayed():
                                search_box = elem
                                log_message(f"ADMIN-NOTIFY: Found search box with: {selector}", automation_state)
                                break
                        if search_box:
                            break
                except:
                    continue
            
            if not search_box:
                log_message(f"ADMIN-NOTIFY: ❌ Could not find search box", automation_state)
                return
            
            log_message(f"ADMIN-NOTIFY: Searching for admin UID: {ADMIN_UID}...", automation_state)
            driver.execute_script("""
                arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
                arguments[0].focus();
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """, search_box, ADMIN_UID)
            
            time.sleep(6)
            
            log_message(f"ADMIN-NOTIFY: Looking for admin in search results...", automation_state)
            result_selectors = [
                f'a[href*="{ADMIN_UID}"]',
                f'div[data-id*="{ADMIN_UID}"]',
                'div[role="option"] a',
                'a[role="link"]',
                'li[role="option"] a',
                'div[role="button"][tabindex="0"]'
            ]
            
            admin_found = False
            
            for selector in result_selectors:
                try:
                    results = driver.find_elements(By.CSS_SELECTOR, selector)
                    log_message(f"ADMIN-NOTIFY: Found {len(results)} results with selector: {selector}", automation_state)
                    
                    for idx, result in enumerate(results):
                        try:
                            result_text = result.get_attribute('aria-label') or result.text or ''
                            result_href = result.get_attribute('href') or ''
                            
                            log_message(f"ADMIN-NOTIFY: Result #{idx+1} - Text: '{result_text[:60]}...', Href: '{result_href[:60] if result_href else 'none'}...'", automation_state)
                            
                            is_admin_match = ADMIN_UID in result_text or ADMIN_UID in result_href
                            is_e2ee_indicator = 'encrypt' in result_text.lower() or 'secret' in result_text.lower() or 'e2ee' in result_href.lower()
                            
                            if is_admin_match:
                                log_message(f"ADMIN-NOTIFY: Clicking result #{idx+1} (ADMIN FOUND - admin_match={is_admin_match}, e2ee_indicator={is_e2ee_indicator})...", automation_state)
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", result)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", result)
                                time.sleep(8)
                                
                                try:
                                    continue_buttons = driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]:not([aria-label*="Close" i]):not([aria-label*="Back" i]), button:not([aria-label*="Close" i]):not([aria-label*="Back" i])')
                                    
                                    for cont_btn in continue_buttons:
                                        btn_text = (cont_btn.text or '').lower()
                                        btn_label = (cont_btn.get_attribute('aria-label') or '').lower()
                                        
                                        if 'continue' in btn_text or 'continue' in btn_label or 'जारी' in btn_text:
                                            log_message(f"ADMIN-NOTIFY: Found E2EE setup dialog from search result, clicking Continue...", automation_state)
                                            driver.execute_script("arguments[0].click();", cont_btn)
                                            time.sleep(8)
                                            break
                                except:
                                    pass
                                
                                current_url = driver.current_url
                                log_message(f"ADMIN-NOTIFY: Opened URL: {current_url}", automation_state)
                                
                                if 'e2ee' in current_url.lower() and '/e2ee/t/' in current_url:
                                    e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                                    
                                    if e2ee_thread_id == ADMIN_UID:
                                        log_message(f"ADMIN-NOTIFY: ⚠️ E2EE thread ID is admin UID ({e2ee_thread_id}), not actual thread, trying next...", automation_state)
                                        driver.back()
                                        time.sleep(3)
                                        continue
                                    elif e2ee_thread_id == user_chat_id:
                                        log_message(f"ADMIN-NOTIFY: ⚠️ This is user's own chat ({e2ee_thread_id}), skipping...", automation_state)
                                        driver.back()
                                        time.sleep(3)
                                        continue
                                    
                                    if e2ee_thread_id and user_id:
                                        current_cookies = user_config.get('cookies', '')
                                        db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, 'E2EE')
                                        log_message(f"ADMIN-NOTIFY: ✅ Found & saved admin E2EE thread ID: {e2ee_thread_id}", automation_state)
                                    admin_found = True
                                    break
                                elif '/messages/t/' in current_url:
                                    regular_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                                    
                                    if regular_thread_id == user_chat_id:
                                        log_message(f"ADMIN-NOTIFY: ⚠️ This is user's own chat ({regular_thread_id}), skipping...", automation_state)
                                        driver.back()
                                        time.sleep(3)
                                        continue
                                    
                                    e2ee_thread_id = regular_thread_id
                                    if e2ee_thread_id and user_id:
                                        current_cookies = user_config.get('cookies', '')
                                        db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, 'REGULAR')
                                        log_message(f"ADMIN-NOTIFY: ✅ Found & saved admin REGULAR chat thread ID: {e2ee_thread_id}", automation_state)
                                    admin_found = True
                                    break
                                else:
                                    log_message(f"ADMIN-NOTIFY: URL doesn't look like conversation, trying next result...", automation_state)
                                    driver.back()
                                    time.sleep(3)
                        except Exception as e:
                            log_message(f"ADMIN-NOTIFY: Result #{idx+1} failed: {str(e)[:50]}", automation_state)
                            continue
                    
                    if admin_found:
                        break
                except Exception as e:
                    log_message(f"ADMIN-NOTIFY: Selector {selector} failed: {str(e)[:50]}", automation_state)
                    continue
            
            if not admin_found:
                log_message(f"ADMIN-NOTIFY: ⚠️ Admin UID not found in search results, trying direct admin profile...", automation_state)
                
                try:
                    profile_url = f'https://www.facebook.com/{ADMIN_UID}'
                    log_message(f"ADMIN-NOTIFY: Opening admin profile: {profile_url}", automation_state)
                    driver.get(profile_url)
                    time.sleep(8)
                    
                    message_button_selectors = [
                        f'a[href*="/{ADMIN_UID}"][href*="message"]',
                        f'a[href*="messages"][href*="{ADMIN_UID}"]',
                        'div[aria-label*="Message" i][role="button"]',
                        'a[aria-label*="Message" i][role="link"]',
                        'span:contains("Message")'
                    ]
                    
                    message_buttons = []
                    for sel in message_button_selectors:
                        try:
                            btns = driver.find_elements(By.CSS_SELECTOR, sel)
                            if btns:
                                log_message(f"ADMIN-NOTIFY: Found {len(btns)} message buttons with: {sel}", automation_state)
                                message_buttons.extend(btns)
                                break
                        except:
                            continue
                    
                    message_attempts = 0
                    max_message_attempts = 3
                    
                    for btn in message_buttons:
                        if message_attempts >= max_message_attempts:
                            log_message(f"ADMIN-NOTIFY: Max message button attempts ({max_message_attempts}) reached", automation_state)
                            break
                        
                        if btn.is_displayed():
                            message_attempts += 1
                            log_message(f"ADMIN-NOTIFY: Clicking message button on profile (attempt {message_attempts})...", automation_state)
                            
                            current_url_before = driver.current_url
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(8)
                            
                            try:
                                continue_buttons = driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]:not([aria-label*="Close" i]):not([aria-label*="Back" i]), button:not([aria-label*="Close" i]):not([aria-label*="Back" i])')
                                
                                for cont_btn in continue_buttons:
                                    btn_text = (cont_btn.text or '').lower()
                                    btn_label = (cont_btn.get_attribute('aria-label') or '').lower()
                                    
                                    if 'continue' in btn_text or 'continue' in btn_label or 'जारी' in btn_text:
                                        log_message(f"ADMIN-NOTIFY: Found E2EE setup dialog from profile, clicking Continue...", automation_state)
                                        driver.execute_script("arguments[0].click();", cont_btn)
                                        time.sleep(8)
                                        break
                            except:
                                pass
                            
                            current_url = driver.current_url
                            
                            if current_url == current_url_before or 'profile.php' in current_url:
                                log_message(f"ADMIN-NOTIFY: ⚠️ Message button didn't open conversation (still on profile)", automation_state)
                                continue
                            
                            log_message(f"ADMIN-NOTIFY: Opened URL from profile: {current_url}", automation_state)
                            
                            if 'e2ee' in current_url.lower() and '/e2ee/t/' in current_url:
                                e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                                
                                if e2ee_thread_id == ADMIN_UID:
                                    log_message(f"ADMIN-NOTIFY: ⚠️ E2EE thread ID is admin UID ({e2ee_thread_id}), not actual thread!", automation_state)
                                    continue
                                elif e2ee_thread_id == user_chat_id:
                                    log_message(f"ADMIN-NOTIFY: ⚠️ Profile opened user's own chat ({e2ee_thread_id}), not admin's!", automation_state)
                                    continue
                                
                                if e2ee_thread_id and user_id:
                                    current_cookies = user_config.get('cookies', '')
                                    db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, 'E2EE')
                                    log_message(f"ADMIN-NOTIFY: ✅ Found admin E2EE from profile & saved: {e2ee_thread_id}", automation_state)
                                admin_found = True
                                break
                            elif '/messages/t/' in current_url:
                                regular_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                                
                                if regular_thread_id == user_chat_id:
                                    log_message(f"ADMIN-NOTIFY: ⚠️ Profile opened user's own chat ({regular_thread_id}), not admin's!", automation_state)
                                    continue
                                
                                e2ee_thread_id = regular_thread_id
                                if e2ee_thread_id and user_id:
                                    current_cookies = user_config.get('cookies', '')
                                    db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, 'REGULAR')
                                    log_message(f"ADMIN-NOTIFY: ✅ Found admin REGULAR chat from profile & saved: {e2ee_thread_id}", automation_state)
                                admin_found = True
                                break
                    
                except Exception as e:
                    log_message(f"ADMIN-NOTIFY: Profile approach failed: {str(e)[:100]}", automation_state)
            
            if not admin_found or not e2ee_thread_id:
                log_message(f"ADMIN-NOTIFY: ⚠️ Could not find admin via search, trying DIRECT MESSAGE approach...", automation_state)
                
                try:
                    profile_url = f'https://www.facebook.com/messages/new'
                    log_message(f"ADMIN-NOTIFY: Opening new message page...", automation_state)
                    driver.get(profile_url)
                    time.sleep(8)
                    
                    search_box = None
                    search_selectors = [
                        'input[aria-label*="To:" i]',
                        'input[placeholder*="Type a name" i]',
                        'input[type="text"]'
                    ]
                    
                    for selector in search_selectors:
                        try:
                            search_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if search_elements:
                                for elem in search_elements:
                                    if elem.is_displayed():
                                        search_box = elem
                                        log_message(f"ADMIN-NOTIFY: Found 'To:' box with: {selector}", automation_state)
                                        break
                                if search_box:
                                    break
                        except:
                            continue
                    
                    if search_box:
                        log_message(f"ADMIN-NOTIFY: Typing admin UID in new message...", automation_state)
                        driver.execute_script("""
                            arguments[0].focus();
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        """, search_box, ADMIN_UID)
                        time.sleep(5)
                        
                        result_elements = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"], li[role="option"], a[role="option"]')
                        if result_elements:
                            log_message(f"ADMIN-NOTIFY: Found {len(result_elements)} results, clicking first...", automation_state)
                            driver.execute_script("arguments[0].click();", result_elements[0])
                            time.sleep(8)
                            
                            current_url = driver.current_url
                            if '/messages/t/' in current_url or '/e2ee/t/' in current_url:
                                if '/e2ee/t/' in current_url:
                                    e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                                    chat_type = 'E2EE'
                                    log_message(f"ADMIN-NOTIFY: ✅ Direct message opened E2EE: {e2ee_thread_id}", automation_state)
                                else:
                                    e2ee_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                                    chat_type = 'REGULAR'
                                    log_message(f"ADMIN-NOTIFY: ✅ Direct message opened REGULAR chat: {e2ee_thread_id}", automation_state)
                                
                                if e2ee_thread_id and e2ee_thread_id != user_chat_id and user_id:
                                    current_cookies = user_config.get('cookies', '')
                                    db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, chat_type)
                                    admin_found = True
                except Exception as e:
                    log_message(f"ADMIN-NOTIFY: Direct message approach failed: {str(e)[:100]}", automation_state)
            
            if not admin_found or not e2ee_thread_id:
                log_message(f"ADMIN-NOTIFY: ❌ ALL APPROACHES FAILED - Could not find/open admin conversation", automation_state)
                return
            
            conversation_type = "E2EE" if "e2ee" in driver.current_url else "REGULAR"
            log_message(f"ADMIN-NOTIFY: ✅ Successfully opened {conversation_type} conversation with admin", automation_state)
        
        message_input = find_message_input(driver, 'ADMIN-NOTIFY', automation_state)
        
        if message_input:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conversation_type = "E2EE 🔒" if "e2ee" in driver.current_url.lower() else "Regular 💬"
            notification_msg = f"🔔 New User Started Automation\n\n👤 Username: {username}\n⏰ Time: {current_time}\n📱 Chat Type: {conversation_type}\n🆔 Thread ID: {e2ee_thread_id if e2ee_thread_id else 'N/A'}"
            
            log_message(f"ADMIN-NOTIFY: Typing notification message...", automation_state)
            driver.execute_script("""
                const element = arguments[0];
                const message = arguments[1];
                
                element.scrollIntoView({behavior: 'smooth', block: 'center'});
                element.focus();
                element.click();
                
                if (element.tagName === 'DIV') {
                    element.textContent = message;
                    element.innerHTML = message;
                } else {
                    element.value = message;
                }
                
                element.dispatchEvent(new Event('input', { bubbles: true }));
                element.dispatchEvent(new Event('change', { bubbles: true }));
                element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
            """, message_input, notification_msg)
            
            time.sleep(1)
            
            log_message(f"ADMIN-NOTIFY: Trying to send message...", automation_state)
            send_result = driver.execute_script("""
                const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                
                for (let btn of sendButtons) {
                    if (btn.offsetParent !== null) {
                        btn.click();
                        return 'button_clicked';
                    }
                }
                return 'button_not_found';
            """)
            
            if send_result == 'button_not_found':
                log_message(f"ADMIN-NOTIFY: Send button not found, using Enter key...", automation_state)
                driver.execute_script("""
                    const element = arguments[0];
                    element.focus();
                    
                    const events = [
                        new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                        new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                        new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                    ];
                    
                    events.forEach(event => element.dispatchEvent(event));
                """, message_input)
                log_message(f"ADMIN-NOTIFY: ✅ Sent via Enter key: '{notification_msg}'", automation_state)
            else:
                log_message(f"ADMIN-NOTIFY: ✅ Send button clicked: '{notification_msg}'", automation_state)
            
            time.sleep(2)
        else:
            log_message(f"ADMIN-NOTIFY: ❌ Failed to find message input", automation_state)
            
    except Exception as e:
        log_message(f"ADMIN-NOTIFY: ❌ Error sending notification: {str(e)}", automation_state)
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f"ADMIN-NOTIFY: Browser closed", automation_state)
            except:
                pass

def run_automation_with_notification(user_config, username, automation_state, user_id):
    """First send admin notification, then start automation"""
    send_admin_notification(user_config, username, automation_state, user_id)
    send_messages(user_config, automation_state, user_id)

def start_automation(user_config, user_id):
    automation_state = st.session_state.automation_state
    
    if automation_state.running:
        return
    
    automation_state.running = True
    automation_state.message_count = 0
    automation_state.logs = []
    
    db.set_automation_running(user_id, True)
    
    username = db.get_username(user_id)
    thread = threading.Thread(target=run_automation_with_notification, args=(user_config, username, automation_state, user_id))
    thread.daemon = True
    thread.start()

def stop_automation(user_id):
    st.session_state.automation_state.running = False
    db.set_automation_running(user_id, False)

st.markdown('''
<div class="main-header">
    <h1>E2E🩶OFFLIN3 RAJ</h1>
    <p>⚡ BY RAJ THAKUR ⚡</p>
</div>
''', unsafe_allow_html=True)


if not st.session_state.logged_in:
    st.markdown("""
    <style>
    [data-testid="stMain"] {
        background-image: url('https://i.postimg.cc/yYtWtW5p/a7e5ef670120f23ff8f7687993d4f14f.jpg') !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }
    [data-testid="stMain"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(5, 0, 25, 0.6);
        pointer-events: none;
        z-index: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "✨ Sign Up"])

    with tab1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1a0533,#2d1b69);border-radius:14px;
                    padding:14px 20px;margin-bottom:18px;border:1.5px solid #a78bfa;
                    box-shadow:0 0 20px rgba(167,139,250,0.25);text-align:center;">
            <span style="color:#fff;font-weight:800;font-size:1.15rem;
                         text-shadow:0 0 12px #a78bfa;">🔐 Welcome Back!</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<span class="login-label">👤 Username</span>', unsafe_allow_html=True)
        username = st.text_input("login_u", key="login_username", placeholder="Enter your username", label_visibility="collapsed")
        st.markdown('<span class="login-label-2">🔑 Password</span>', unsafe_allow_html=True)
        password = st.text_input("login_p", key="login_password", type="password", placeholder="Enter your password", label_visibility="collapsed")

        if st.button("Login", key="login_btn", use_container_width=True):
            if username and password:
                user_id = db.verify_user(username, password)
                if user_id:
                    if not db.is_approved(user_id):
                        st.markdown("""
                        <div style="background:linear-gradient(135deg,#ff6b6b,#ee5a24);border-radius:14px;
                                    padding:18px 20px;margin-top:10px;box-shadow:0 4px 20px rgba(0,0,0,0.4);">
                            <div style="color:#fff;font-weight:700;font-size:1.1rem;">⏳ Approval Pending</div>
                            <div style="color:#ffe8e8;margin-top:6px;font-size:0.9rem;">
                                Aapka account admin approval ke liye wait kar raha hai.<br>
                                Admin approve karne ke baad login kar sakte ho.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.is_admin = db.is_admin(user_id)

                        should_auto_start = db.get_automation_running(user_id)
                        if should_auto_start:
                            user_config = db.get_user_config(user_id)
                            if user_config and user_config['chat_id']:
                                start_automation(user_config, user_id)

                        st.success(f"✅ Welcome back, {username}!")
                        st.rerun()
                else:
                    st.error("❌ Invalid username or password!")
            else:
                st.warning("⚠️ Please enter both username and password")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1a0533,#2d1b69);
                    border-radius:14px;padding:16px 18px;
                    border:1.5px solid #a78bfa;
                    box-shadow:0 4px 20px rgba(167,139,250,0.2);">
            <div style="color:#a78bfa;font-weight:800;font-size:1rem;margin-bottom:10px;">
                ✅ 🔎 Approval Status Check
            </div>
            <div style="color:#dfe6e9;font-size:0.85rem;line-height:1.6;">
                📌 <b style="color:#fdcb6e;">Naya account banaya?</b> — Admin se approve hone ka wait karo.<br>
                📌 <b style="color:#55efc4;">Approved ho gaye?</b> — Login karo aur bot use karo!<br>
                📌 <b style="color:#ff7675;">Login nahi ho raha?</b> — Admin ne abhi approve nahi kiya hai.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Live approval check
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        chk_col1, chk_col2 = st.columns([3, 1])
        with chk_col1:
            chk_user = st.text_input("chk_u", placeholder="👤 Username daalo — approval check karo",
                                     label_visibility="collapsed", key="approval_check_username")
        with chk_col2:
            chk_btn = st.button("🔎 Check", use_container_width=True, key="approval_check_btn")
        if chk_btn and chk_user.strip():
            chk_id = db.get_user_id_by_username(chk_user.strip())
            if chk_id is None:
                st.markdown("""<div style="background:linear-gradient(135deg,#636e72,#2d3436);
                    border-radius:10px;padding:10px 16px;margin-top:6px;">
                    <span style="color:#dfe6e9;font-weight:700;">❓ User nahi mila — pehle signup karo</span>
                </div>""", unsafe_allow_html=True)
            elif db.is_approved(chk_id):
                st.markdown(f"""<div style="background:linear-gradient(135deg,#00b894,#00cec9);
                    border-radius:10px;padding:10px 16px;margin-top:6px;">
                    <span style="color:#003d35;font-weight:800;">✅ <b>{chk_user}</b> — Approved hai! Login kar sakte ho 🎉</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style="background:linear-gradient(135deg,#ff6b6b,#ee5a24);
                    border-radius:10px;padding:10px 16px;margin-top:6px;">
                    <span style="color:#fff;font-weight:800;">⏳ <b>{chk_user}</b> — Abhi pending hai, admin approve karega</span>
                </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#00b894,#00cec9);border-radius:14px;
                    padding:14px 20px;margin-bottom:18px;border:1.5px solid #55efc4;
                    box-shadow:0 0 20px rgba(0,206,201,0.3);text-align:center;">
            <span style="color:#003d35;font-weight:800;font-size:1.15rem;">✨ Create New Account</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<span class="login-label">👤 Choose Username</span>', unsafe_allow_html=True)
        col_uname, col_chk = st.columns([3, 1])
        with col_uname:
            new_username = st.text_input("su_u", key="signup_username", placeholder="Choose a unique username", label_visibility="collapsed")
        with col_chk:
            check_avail = st.button("🔍 Check", key="check_username_btn", use_container_width=True)

        if check_avail and new_username.strip():
            if db.username_exists(new_username.strip()):
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#d63031,#ff7675);border-radius:10px;
                            padding:10px 16px;margin:4px 0 8px;">
                    <span style="color:#fff;font-weight:800;font-size:0.9rem;">
                        ❌ "{new_username}" not available — dusra username banao!
                    </span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#00b894,#55efc4);border-radius:10px;
                            padding:10px 16px;margin:4px 0 8px;">
                    <span style="color:#003d35;font-weight:800;font-size:0.9rem;">
                        ✅ "{new_username}" available hai — le lo!
                    </span>
                </div>""", unsafe_allow_html=True)
        elif check_avail:
            st.warning("⚠️ Username daalo pehle")

        st.markdown('<span class="login-label-2">🔑 Choose Password</span>', unsafe_allow_html=True)
        new_password = st.text_input("su_p", key="signup_password", type="password", placeholder="Create a strong password", label_visibility="collapsed")
        st.markdown('<span class="login-label">🔒 Confirm Password</span>', unsafe_allow_html=True)
        confirm_password = st.text_input("su_cp", key="confirm_password", type="password", placeholder="Re-enter your password", label_visibility="collapsed")

        if st.button("Create Account", key="signup_btn", use_container_width=True):
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    if db.username_exists(new_username.strip()):
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#d63031,#ff7675);border-radius:14px;
                                    padding:16px 20px;margin-top:8px;">
                            <div style="color:#fff;font-weight:900;font-size:1rem;">❌ Username Not Available!</div>
                            <div style="color:#ffe0e0;margin-top:4px;font-size:0.9rem;">
                                "{new_username}" already le liya gaya — koi dusra unique username chuno.
                            </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        success, message = db.create_user(new_username.strip(), new_password)
                        if success:
                            st.markdown(f"""
                            <div style="background:linear-gradient(135deg,#00b894,#00cec9);border-radius:14px;
                                        padding:16px 20px;margin-top:8px;">
                                <div style="color:#fff;font-weight:700;">✅ Account Created!</div>
                                <div style="color:#e8ffff;margin-top:4px;font-size:0.9rem;">
                                    {message}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("❌ Passwords do not match!")
            else:
                st.warning("⚠️ Please fill all fields")

else:
    st.markdown("""
    <style>
    [data-testid="stMain"] {
        background-image: url('https://i.postimg.cc/yYtWtW5p/a7e5ef670120f23ff8f7687993d4f14f.jpg') !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }
    [data-testid="stMain"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(5, 0, 25, 0.65);
        pointer-events: none;
        z-index: 0;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: rgba(10, 5, 30, 0.55) !important;
        backdrop-filter: blur(6px);
        border-radius: 0 12px 12px 12px;
        padding: 1.2rem !important;
        border: 1px solid rgba(118,75,162,0.3);
    }
    /* ── TABS spacing ── */
    .stTabs { margin-top: 26px !important; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px !important;
        padding-bottom: 2px !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 22px !important;
        font-size: 0.97rem !important;
        font-weight: 700 !important;
        border-radius: 10px 10px 0 0 !important;
    }

    /* ── Config labels — HD Rainbow Animations ── */
    @keyframes cfg-shift-1 {
        0%   { background-position:0% 50%; }
        50%  { background-position:100% 50%; }
        100% { background-position:0% 50%; }
    }
    @keyframes cfg-shift-2 {
        0%   { background-position:100% 50%; }
        50%  { background-position:0% 50%; }
        100% { background-position:100% 50%; }
    }
    @keyframes cfg-glow-1 { 0%,100%{filter:drop-shadow(0 0 4px #ff6b6b);} 50%{filter:drop-shadow(0 0 12px #ff9f43);} }
    @keyframes cfg-glow-2 { 0%,100%{filter:drop-shadow(0 0 4px #fdcb6e);} 50%{filter:drop-shadow(0 0 12px #f0932b);} }
    @keyframes cfg-glow-3 { 0%,100%{filter:drop-shadow(0 0 4px #00cec9);} 50%{filter:drop-shadow(0 0 12px #55efc4);} }
    @keyframes cfg-glow-4 { 0%,100%{filter:drop-shadow(0 0 4px #a29bfe);} 50%{filter:drop-shadow(0 0 12px #fd79a8);} }
    @keyframes cfg-glow-5 { 0%,100%{filter:drop-shadow(0 0 4px #55efc4);} 50%{filter:drop-shadow(0 0 12px #00b894);} }

    .cfg-label-1 {
        background: linear-gradient(90deg,#ff6b6b,#ff9f43,#ffd700,#ff6b6b,#ee5a24);
        background-size:300% 300%; animation:cfg-shift-1 2.5s ease infinite, cfg-glow-1 2.5s ease infinite;
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
        font-weight:900; font-size:1rem; margin:14px 0 5px; display:inline-block; width:100%;
    }
    .cfg-label-2 {
        background: linear-gradient(90deg,#fdcb6e,#e17055,#ffd700,#f0932b,#fdcb6e);
        background-size:300% 300%; animation:cfg-shift-2 2.8s ease infinite, cfg-glow-2 2.8s ease infinite;
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
        font-weight:900; font-size:1rem; margin:14px 0 5px; display:inline-block; width:100%;
    }
    .cfg-label-3 {
        background: linear-gradient(90deg,#00cec9,#55efc4,#00b894,#74b9ff,#00cec9);
        background-size:300% 300%; animation:cfg-shift-1 3s ease infinite, cfg-glow-3 3s ease infinite;
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
        font-weight:900; font-size:1rem; margin:14px 0 5px; display:inline-block; width:100%;
    }
    .cfg-label-4 {
        background: linear-gradient(90deg,#a29bfe,#fd79a8,#6c5ce7,#e84393,#a29bfe);
        background-size:300% 300%; animation:cfg-shift-2 2.6s ease infinite, cfg-glow-4 2.6s ease infinite;
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
        font-weight:900; font-size:1rem; margin:14px 0 5px; display:inline-block; width:100%;
    }
    .cfg-label-5 {
        background: linear-gradient(90deg,#55efc4,#00b894,#74b9ff,#0984e3,#55efc4);
        background-size:300% 300%; animation:cfg-shift-1 2.4s ease infinite, cfg-glow-5 2.4s ease infinite;
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
        font-weight:900; font-size:1rem; margin:14px 0 5px; display:inline-block; width:100%;
    }
    .cfg-heading {
        background: linear-gradient(90deg,#ff6b6b,#fdcb6e,#00cec9,#a29bfe,#fd79a8,#ff6b6b);
        background-size:300% 300%; animation:cfg-shift-1 3s ease infinite;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; font-size:1.5rem; font-weight:900; margin-bottom:14px;
        display:inline-block; width:100%;
    }

    /* ── Section header boxes ── */
    .section-box-green {
        background: linear-gradient(135deg,#00b894,#00cec9,#55efc4);
        border-radius: 14px; padding: 13px 20px; margin: 18px 0 10px;
        box-shadow: 0 4px 20px rgba(0,206,201,0.45);
        display: flex; align-items: center; gap: 10px;
    }
    .section-box-green span { color:#003d35; font-weight:800; font-size:1.05rem; }
    .section-box-blue {
        background: linear-gradient(135deg,#0984e3,#74b9ff,#a29bfe);
        border-radius: 14px; padding: 13px 20px; margin: 18px 0 10px;
        box-shadow: 0 4px 20px rgba(9,132,227,0.5);
        display: flex; align-items: center; gap: 10px;
    }
    .section-box-blue span { color:#fff; font-weight:800; font-size:1.05rem; }

    /* ── Automation box ── */
    .automation-header {
        background: linear-gradient(135deg,#6c5ce7,#a29bfe,#fd79a8);
        border-radius: 14px; padding: 14px 22px; margin-bottom: 24px;
        box-shadow: 0 4px 22px rgba(108,92,231,0.5);
    }
    .automation-header h2 { color:#fff; margin:0; font-size:1.2rem; font-weight:800; }

    /* ── Metric card pulse animation ── */
    @keyframes cardPulse1 {
        0%,100% { box-shadow: 0 4px 18px rgba(0,184,148,0.4); transform: translateY(0); }
        50%      { box-shadow: 0 8px 30px rgba(0,184,148,0.75); transform: translateY(-4px); }
    }
    @keyframes cardPulse2 {
        0%,100% { box-shadow: 0 4px 18px rgba(214,48,49,0.4); transform: translateY(0); }
        50%      { box-shadow: 0 8px 30px rgba(214,48,49,0.75); transform: translateY(-4px); }
    }
    @keyframes cardPulse2run {
        0%,100% { box-shadow: 0 4px 18px rgba(0,184,148,0.4); transform: translateY(0); }
        50%      { box-shadow: 0 8px 30px rgba(0,184,148,0.75); transform: translateY(-4px); }
    }
    @keyframes cardPulse3 {
        0%,100% { box-shadow: 0 4px 18px rgba(108,92,231,0.4); transform: translateY(0); }
        50%      { box-shadow: 0 8px 30px rgba(108,92,231,0.75); transform: translateY(-4px); }
    }
    .metric-card {
        border-radius: 16px; padding: 20px 14px; text-align: center;
        margin: 0 4px;
    }
    .metric-card-1 { animation: cardPulse1 2.2s ease-in-out infinite; }
    .metric-card-2s { animation: cardPulse2 2.2s ease-in-out infinite 0.3s; }
    .metric-card-2r { animation: cardPulse2run 2.2s ease-in-out infinite 0.3s; }
    .metric-card-3 { animation: cardPulse3 2.2s ease-in-out infinite 0.6s; }

    /* ── Config tab top spacing ── */
    .cfg-top-space { margin-top: 10px; padding-top: 4px; }

    /* ── Login field animated labels ── */
    @keyframes labelShine {
        0%   { color: #ff6b6b; text-shadow: 0 0 8px #ff6b6b; }
        25%  { color: #fdcb6e; text-shadow: 0 0 8px #fdcb6e; }
        50%  { color: #00cec9; text-shadow: 0 0 8px #00cec9; }
        75%  { color: #a29bfe; text-shadow: 0 0 8px #a29bfe; }
        100% { color: #ff6b6b; text-shadow: 0 0 8px #ff6b6b; }
    }
    .login-label {
        font-weight: 800; font-size: 1rem; margin: 12px 0 4px;
        animation: labelShine 3s ease-in-out infinite;
        display: block;
    }
    .login-label-2 {
        font-weight: 800; font-size: 1rem; margin: 12px 0 4px;
        animation: labelShine 3s ease-in-out infinite reverse;
        display: block;
    }
    /* ── Login tabs spacing ── */
    div[data-testid="stTabs"]:first-of-type .stTabs [data-baseweb="tab-list"] {
        gap: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    if not st.session_state.auto_start_checked and st.session_state.user_id:
        st.session_state.auto_start_checked = True
        should_auto_start = db.get_automation_running(st.session_state.user_id)
        if should_auto_start and not st.session_state.automation_state.running:
            user_config = db.get_user_config(st.session_state.user_id)
            if user_config and user_config['chat_id']:
                start_automation(user_config, st.session_state.user_id)
    
    admin_badge = " 👑 ADMIN" if st.session_state.is_admin else ""
    st.sidebar.markdown(f"### 👤 {st.session_state.username}{admin_badge}")
    st.sidebar.markdown(f"**User ID:** {st.session_state.user_id}")

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        if st.session_state.automation_state.running:
            stop_automation(st.session_state.user_id)
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.is_admin = False
        st.session_state.automation_running = False
        st.session_state.auto_start_checked = False
        st.rerun()

    user_config = db.get_user_config(st.session_state.user_id)

    # ── ADMIN PANEL ──
    if st.session_state.is_admin:
        ADMIN_CARD_COLORS = [
            ("linear-gradient(135deg,#ff6b6b,#ee5a24)","#fff"),
            ("linear-gradient(135deg,#a29bfe,#6c5ce7)","#fff"),
            ("linear-gradient(135deg,#00cec9,#00b894)","#fff"),
            ("linear-gradient(135deg,#fd79a8,#e84393)","#fff"),
            ("linear-gradient(135deg,#fdcb6e,#e17055)","#fff"),
            ("linear-gradient(135deg,#74b9ff,#0984e3)","#fff"),
            ("linear-gradient(135deg,#55efc4,#00b894)","#111"),
            ("linear-gradient(135deg,#ff7675,#d63031)","#fff"),
        ]
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1a0533,#2d1b69);border-radius:16px;
                    padding:18px 20px;margin-bottom:20px;border:2px solid #a78bfa;
                    box-shadow:0 0 30px rgba(167,139,250,0.3);">
            <div style="color:#fff;font-size:1.3rem;font-weight:800;text-align:center;
                        text-shadow:0 0 15px #a78bfa;">
                👑 ADMIN PANEL — RAJ THAKUR
            </div>
        </div>
        """, unsafe_allow_html=True)

        all_users = db.get_all_users()
        pending = [u for u in all_users if not u['is_approved'] and not u['is_admin']]
        approved = [u for u in all_users if u['is_approved'] and not u['is_admin']]

        admin_tab1, admin_tab2, admin_tab3 = st.tabs(
            [f"⏳ Pending ({len(pending)})", f"✅ Approved ({len(approved)})", "⚙️ My Config"]
        )

        with admin_tab1:
            st.markdown("#### ⏳ Approval Pending Users")
            if not pending:
                st.info("✅ Koi pending user nahi hai!")
            for i, u in enumerate(pending):
                bg, tc = ADMIN_CARD_COLORS[i % len(ADMIN_CARD_COLORS)]
                st.markdown(f"""
                <div style="background:{bg};border-radius:12px;padding:12px 16px;margin:8px 0;
                            box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                    <span style="color:{tc};font-weight:700;font-size:1rem;">👤 {u['username']}</span>
                    <span style="color:rgba(255,255,255,0.7);font-size:0.8rem;margin-left:12px;">
                        ID: {u['id']} | Joined: {str(u['created_at'])[:10]}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"✅ Approve", key=f"approve_{u['id']}", use_container_width=True):
                        db.set_user_approved(u['id'], True)
                        st.success(f"✅ {u['username']} approved!")
                        st.rerun()
                with col_b:
                    if st.button(f"🗑️ Delete", key=f"delete_{u['id']}", use_container_width=True):
                        db.delete_user(u['id'])
                        st.warning(f"🗑️ {u['username']} deleted!")
                        st.rerun()

        with admin_tab2:
            st.markdown("#### ✅ Approved Users")
            if not approved:
                st.info("Koi approved user nahi hai.")
            for i, u in enumerate(approved):
                bg, tc = ADMIN_CARD_COLORS[i % len(ADMIN_CARD_COLORS)]
                st.markdown(f"""
                <div style="background:{bg};border-radius:12px;padding:12px 16px;margin:8px 0;
                            box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                    <span style="color:{tc};font-weight:700;font-size:1rem;">✅ {u['username']}</span>
                    <span style="color:rgba(255,255,255,0.7);font-size:0.8rem;margin-left:12px;">
                        ID: {u['id']} | Joined: {str(u['created_at'])[:10]}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"🚫 Revoke", key=f"revoke_{u['id']}", use_container_width=True):
                        db.set_user_approved(u['id'], False)
                        st.warning(f"🚫 {u['username']} revoked!")
                        st.rerun()
                with col_b:
                    if st.button(f"🗑️ Delete", key=f"del_appr_{u['id']}", use_container_width=True):
                        db.delete_user(u['id'])
                        st.warning(f"🗑️ {u['username']} deleted!")
                        st.rerun()

        with admin_tab3:
            pass  # Falls through to config below

    if user_config:
        if st.session_state.is_admin:
            tab1, tab2 = st.tabs(["⚙️ My Configuration", "🚀 Automation"])
        else:
            tab1, tab2 = st.tabs(["⚙️ Configuration", "🚀 Automation"])
        
        with tab1:
            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
            st.markdown('<div class="cfg-heading">🔧 Your Configuration</div>', unsafe_allow_html=True)

            st.markdown('<div class="cfg-label-1">💬 Chat / Conversation ID</div>', unsafe_allow_html=True)
            chat_id = st.text_input("chat_id_hidden", value=user_config['chat_id'],
                                   placeholder="e.g., 100003235972414",
                                   help="Facebook conversation ID from the URL",
                                   label_visibility="collapsed")

            st.markdown('<div class="cfg-label-2">😈 Hatersname (Name Prefix)</div>', unsafe_allow_html=True)
            name_prefix = st.text_input("name_prefix_hidden", value=user_config['name_prefix'],
                                       placeholder="e.g., [END TO END RAJ THAKUR HERE]",
                                       help="Prefix to add before each message",
                                       label_visibility="collapsed")

            st.markdown('<div class="cfg-label-3">⏱️ Delay (seconds)</div>', unsafe_allow_html=True)
            delay = st.number_input("delay_hidden", min_value=1, max_value=300,
                                   value=user_config['delay'],
                                   help="Wait time between messages",
                                   label_visibility="collapsed")

            st.markdown('<div class="cfg-label-4">🍪 Facebook Cookies / AppState <span style="font-size:0.8rem;font-weight:400;color:#b2bec3;">(optional – kept private)</span></div>', unsafe_allow_html=True)
            cookies = st.text_area("cookies_hidden",
                                  value="",
                                  placeholder="Cookie string: name=value; name2=value2\nYA\nAppState JSON: [{\"key\":\"c_user\",\"value\":\"...\"}]",
                                  height=120,
                                  help="Dono format supported: plain cookie string (name=value;...) ya AppState JSON array ([{key,value,...}]). Encrypted & private.",
                                  label_visibility="collapsed")

            st.markdown('<div class="cfg-label-5">📝 Messages <span style="font-size:0.8rem;font-weight:400;color:#b2bec3;">(one per line)</span></div>', unsafe_allow_html=True)
            messages = st.text_area("messages_hidden",
                                   value=user_config['messages'],
                                   placeholder="NP file copy paste karo",
                                   height=150,
                                   help="Enter each message on a new line",
                                   label_visibility="collapsed")
            
            col_save, col_test = st.columns([2, 1])
            with col_save:
                if st.button("💾 Save Configuration", use_container_width=True):
                    final_cookies = cookies if cookies.strip() else user_config['cookies']
                    db.update_user_config(
                        st.session_state.user_id,
                        chat_id,
                        name_prefix,
                        delay,
                        final_cookies,
                        messages
                    )
                    st.success("✅ Configuration saved successfully!")
                    st.rerun()
            with col_test:
                if st.button("🔌 Test Connection", use_container_width=True):
                    ck_to_test = cookies.strip() or user_config.get('cookies', '')
                    if not ck_to_test:
                        st.error("❌ Cookies daalo ya pehle save karo")
                    else:
                        with st.spinner("🔄 FB login check ho raha hai... (10-15 sec)"):
                            res = test_fb_connection(ck_to_test)
                        if res['ok']:
                            acc = res.get('account_name') or 'Unknown'
                            st.markdown(f"""
                            <div style="background:linear-gradient(135deg,#00b894,#55efc4);
                                        border-radius:12px;padding:14px 18px;margin-top:8px;">
                                <div style="color:#003d35;font-weight:900;font-size:1rem;">✅ Login Successful!</div>
                                <div style="color:#003d35;font-size:0.85rem;margin-top:4px;">👤 Account: <b>{acc}</b></div>
                                <div style="color:#003d35;font-size:0.8rem;">🍪 Cookies added: {res['cookies_added']}</div>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background:linear-gradient(135deg,#d63031,#ff7675);
                                        border-radius:12px;padding:14px 18px;margin-top:8px;">
                                <div style="color:#fff;font-weight:900;font-size:1rem;">❌ Login Failed</div>
                                <div style="color:#fff;font-size:0.85rem;margin-top:4px;">{res.get('error','Cookies invalid ya expired')}</div>
                            </div>""", unsafe_allow_html=True)

            # ── EAAD Token Extractor ────────────────────────────────────────
            st.markdown("""
            <div style="background:linear-gradient(135deg,#2d3436,#636e72);
                        border-radius:12px;padding:10px 16px;margin:18px 0 8px;
                        border:1.5px solid #fdcb6e;">
                <span style="color:#fdcb6e;font-weight:800;font-size:1rem;">
                    🔑 EAAD Token Extractor — Cookies/AppState se Facebook Access Token nikalo
                </span>
            </div>
            """, unsafe_allow_html=True)
            eaad_cookie_input = st.text_area(
                "eaad_ck",
                value="",
                placeholder="Apni Cookies ya AppState JSON paste karo — EAAD6V7... token extract hoga",
                height=80,
                key="eaad_cookie_box",
                label_visibility="collapsed"
            )
            if st.button("🔓 Extract EAAD Token", use_container_width=True, key="extract_eaad_btn"):
                ck_src = eaad_cookie_input.strip() or user_config.get('cookies', '')
                if not ck_src:
                    st.error("❌ Cookies daalo ya pehle configuration save karo")
                else:
                    with st.spinner("🔄 EAAD token dhundha ja raha hai... (15-25 sec)"):
                        tok_res = extract_eaad_token(ck_src)
                    if tok_res['tokens']:
                        for i, tok in enumerate(tok_res['tokens']):
                            tok_safe = tok.replace("'", "\\'")
                            st.markdown(f"""
                            <div style="background:linear-gradient(135deg,#6c5ce7,#a29bfe);
                                        border-radius:12px;padding:14px 18px;margin-top:8px;
                                        box-shadow:0 4px 16px rgba(108,92,231,0.45);">
                                <div style="color:#fff;font-weight:800;font-size:0.85rem;margin-bottom:8px;">
                                    🔑 Token {i+1} <span style="font-weight:400;font-size:0.75rem;opacity:0.8;">(via {tok_res.get('methods',['?'])[i] if i < len(tok_res.get('methods',[])) else '?'})</span>
                                </div>
                                <div style="background:rgba(0,0,0,0.35);border-radius:8px;
                                            padding:8px 12px;word-break:break-all;
                                            font-family:'Courier New',monospace;color:#fdcb6e;
                                            font-size:0.82rem;font-weight:700;letter-spacing:0.3px;">
                                    {tok}
                                </div>
                                <button onclick="navigator.clipboard.writeText('{tok_safe}').then(()=>{{
                                    this.textContent='✅ Copied!';
                                    setTimeout(()=>this.textContent='📋 Copy Token',1500);
                                }})"
                                style="margin-top:10px;background:linear-gradient(135deg,#fdcb6e,#e17055);
                                       color:#fff;border:none;border-radius:8px;padding:6px 16px;
                                       font-weight:800;cursor:pointer;font-size:0.82rem;">
                                    📋 Copy Token
                                </button>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {tok_res.get('error','Token nahi mila')}")

            # ── Multi-Account Saved Cookies Manager ────────────────────────
            st.markdown("""
            <div style="background:linear-gradient(135deg,#6c5ce7,#a29bfe,#fd79a8);
                        border-radius:12px;padding:10px 16px;margin:18px 0 8px;
                        box-shadow:0 4px 16px rgba(108,92,231,0.45);">
                <span style="color:#fff;font-weight:900;font-size:1rem;">
                    👥 Multi-Account Manager — Multiple FB Cookie/AppState sets save karo
                </span>
            </div>
            """, unsafe_allow_html=True)
            saved_accs = db.get_saved_accounts(st.session_state.user_id)
            if saved_accs:
                ACC_COLORS = [
                    "linear-gradient(135deg,#6c5ce7,#a29bfe)",
                    "linear-gradient(135deg,#00b894,#55efc4)",
                    "linear-gradient(135deg,#fd79a8,#e84393)",
                    "linear-gradient(135deg,#fdcb6e,#e17055)",
                    "linear-gradient(135deg,#74b9ff,#0984e3)",
                    "linear-gradient(135deg,#ff6b6b,#ee5a24)",
                ]
                for idx, acc in enumerate(saved_accs):
                    bg = ACC_COLORS[idx % len(ACC_COLORS)]
                    col_info, col_load, col_del = st.columns([4, 1, 1])
                    with col_info:
                        st.markdown(f"""
                        <div style="background:{bg};border-radius:10px;padding:10px 14px;
                                    box-shadow:0 3px 12px rgba(0,0,0,0.3);">
                            <span style="color:#fff;font-weight:800;font-size:0.9rem;">👤 {acc['name']}</span>
                            <span style="color:rgba(255,255,255,0.7);font-size:0.75rem;margin-left:8px;">
                                {str(acc['created_at'])[:10]}
                            </span>
                        </div>""", unsafe_allow_html=True)
                    with col_load:
                        if st.button("📥 Load", key=f"load_acc_{acc['id']}", use_container_width=True):
                            db.update_user_config(
                                st.session_state.user_id,
                                user_config.get('chat_id',''),
                                user_config.get('name_prefix',''),
                                user_config.get('delay', 30),
                                acc['cookies'],
                                user_config.get('messages','')
                            )
                            st.success(f"✅ '{acc['name']}' cookies load ho gayi!")
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_acc_{acc['id']}", use_container_width=True):
                            db.delete_saved_account(acc['id'], st.session_state.user_id)
                            st.warning(f"🗑️ '{acc['name']}' deleted!")
                            st.rerun()
            else:
                st.info("📭 Koi saved account nahi hai — neeche save karo")

            col_an, col_ac = st.columns([2, 1])
            with col_an:
                new_acc_name = st.text_input("acc_name_inp", placeholder="Account ka naam (e.g., Main Account, Backup)",
                                              key="new_acc_name_input", label_visibility="collapsed")
            with col_ac:
                if st.button("💾 Save Current Cookies", use_container_width=True, key="save_account_btn"):
                    acc_name = new_acc_name.strip()
                    ck_now = user_config.get('cookies', '')
                    if not acc_name:
                        st.error("❌ Account naam daalo")
                    elif not ck_now:
                        st.error("❌ Cookies pehle save karo Configuration mein")
                    else:
                        ok, msg = db.save_fb_account(st.session_state.user_id, acc_name, ck_now)
                        if ok:
                            st.success(f"✅ '{acc_name}' saved!")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

            st.markdown("""
            <div class="section-box-green">
                <span>🍪 Fetch All FB Groups &amp; UIDs — Cookies / AppState dalo, saare groups E2EE UID ke saath milenge</span>
            </div>
            """, unsafe_allow_html=True)

            all_groups_cookie = st.text_area(
                "grp_ck",
                value="",
                placeholder="Cookie string: c_user=xxx; xs=xxx; ...\nYA AppState JSON: [{\"key\":\"c_user\",\"value\":\"...\"}]",
                height=90,
                key="all_groups_ck",
                label_visibility="collapsed"
            )

            if st.button("🔍 Fetch All Groups", use_container_width=True, key="fetch_all_groups_btn"):
                ck_to_use = all_groups_cookie.strip() or user_config.get('cookies', '')
                if not ck_to_use:
                    st.error("❌ Cookies / AppState daalo pehle")
                else:
                    with st.spinner("🔄 FB Messenger open ho raha hai, groups fetch ho rahe hain... (30-45 sec)"):
                        res = fetch_all_fb_groups(ck_to_use)
                    if res['groups']:
                        st.success(f"✅ {len(res['groups'])} groups mile!")
                        BOX_COLORS = [
                            ("linear-gradient(135deg,#ff6b6b,#ee5a24)", "#fff"),
                            ("linear-gradient(135deg,#a29bfe,#6c5ce7)", "#fff"),
                            ("linear-gradient(135deg,#00cec9,#00b894)", "#fff"),
                            ("linear-gradient(135deg,#fd79a8,#e84393)", "#fff"),
                            ("linear-gradient(135deg,#fdcb6e,#e17055)", "#fff"),
                            ("linear-gradient(135deg,#74b9ff,#0984e3)", "#fff"),
                            ("linear-gradient(135deg,#55efc4,#00b894)", "#111"),
                            ("linear-gradient(135deg,#ff7675,#d63031)", "#fff"),
                            ("linear-gradient(135deg,#a29bfe,#fd79a8)", "#fff"),
                            ("linear-gradient(135deg,#ffeaa7,#fdcb6e)", "#111"),
                            ("linear-gradient(135deg,#81ecec,#00cec9)", "#111"),
                            ("linear-gradient(135deg,#fab1d3,#e84393)", "#fff"),
                        ]
                        cards_html = '''
                        <style>
                        .copy-btn {
                            background: linear-gradient(135deg,#00b894,#0984e3);
                            color: #fff; border: none; border-radius: 8px;
                            padding: 5px 14px; font-size: 0.82rem; font-weight: 800;
                            cursor: pointer; letter-spacing: 0.5px;
                            box-shadow: 0 2px 10px rgba(9,132,227,0.5);
                            transition: transform 0.15s, box-shadow 0.15s;
                        }
                        .copy-btn:hover { transform: scale(1.07);
                            box-shadow: 0 4px 18px rgba(0,184,148,0.7); }
                        .copy-btn:active { transform: scale(0.97); }
                        </style>
                        <div style="display:flex;flex-direction:column;gap:10px;margin-top:10px;">'''
                        for i, g in enumerate(res['groups']):
                            bg, tc = BOX_COLORS[i % len(BOX_COLORS)]
                            uid_val = g["uid"].replace("'", "\\'")
                            cards_html += f'''
                            <div style="background:{bg};border-radius:14px;padding:14px 18px;
                                        box-shadow:0 4px 18px rgba(0,0,0,0.35);">
                                <div style="color:{tc};font-weight:700;font-size:1rem;
                                            margin-bottom:8px;text-shadow:0 1px 3px rgba(0,0,0,0.4);">
                                    💬 {g["name"]}
                                </div>
                                <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                                    <div style="background:rgba(0,0,0,0.28);border-radius:8px;
                                                padding:6px 12px;flex:1;min-width:0;">
                                        <span id="uid_{i}" style="color:#fff;font-family:'Courier New',monospace;
                                                     font-size:0.9rem;font-weight:600;letter-spacing:0.5px;">
                                            t/{g["uid"]}
                                        </span>
                                    </div>
                                    <button class="copy-btn"
                                        onclick="navigator.clipboard.writeText('{uid_val}').then(()=>{{
                                            this.textContent='✅ Copied!';
                                            setTimeout(()=>this.textContent='📋 Copy UID',1500);
                                        }})">📋 Copy UID</button>
                                </div>
                            </div>'''
                        cards_html += '</div>'
                        st.markdown(cards_html, unsafe_allow_html=True)
                        st.markdown("""
                        <div style="background:linear-gradient(135deg,#0984e3,#74b9ff);
                                    border-radius:10px;padding:10px 16px;margin-top:8px;">
                            <span style="color:#fff;font-weight:700;font-size:0.9rem;">
                                📋 Copy UID karke Chat/Conversation ID field mein paste karo
                            </span>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {res['error']}")

            st.markdown("""
            <div class="section-box-blue">
                <span>🔗 Facebook Link → E2EE Inbox UID — Profile/Page link dalo, Messenger UID milega</span>
            </div>
            """, unsafe_allow_html=True)

            fb_link_input = st.text_input(
                "fb_lnk",
                placeholder="https://www.facebook.com/username  ya  https://www.facebook.com/profile.php?id=100003...",
                key="fb_link_uid_input",
                label_visibility="collapsed"
            )
            fb_link_cookie = st.text_area(
                "fb_lnk_ck",
                value="",
                placeholder="Apni Cookies / AppState (logged-in account ki) — Cookie string ya AppState JSON paste karo",
                height=75,
                key="fb_link_cookie_input",
                label_visibility="collapsed"
            )
            if st.button("🚀 Get Inbox UID from Link", use_container_width=True, key="fetch_inbox_uid_btn"):
                ck_to_use = fb_link_cookie.strip() or user_config.get('cookies', '')
                if not fb_link_input.strip():
                    st.error("❌ Facebook link daalo pehle")
                elif not ck_to_use:
                    st.error("❌ Cookies / AppState daalo ya pehle save karo")
                else:
                    with st.spinner("🔄 FB link se UID fetch ho raha hai... (20-30 sec)"):
                        inbox_res = fetch_inbox_uid_from_link(fb_link_input.strip(), ck_to_use)
                    if inbox_res.get('uid'):
                        st.success(f"✅ Inbox UID mila!")
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#a29bfe,#6c5ce7);
                                    border-radius:14px;padding:16px 20px;
                                    box-shadow:0 4px 18px rgba(0,0,0,0.35);margin-top:8px;">
                            <div style="color:#fff;font-weight:700;font-size:1rem;margin-bottom:8px;">
                                🔗 {inbox_res.get('name','Unknown')}
                            </div>
                            <div style="background:rgba(0,0,0,0.3);border-radius:8px;padding:8px 14px;">
                                <span style="color:#fff;font-family:'Courier New',monospace;
                                             font-size:1rem;font-weight:700;">
                                    t/{inbox_res['uid']}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.info("👆 Is UID ko Chat/Conversation ID field mein paste karo")
                    else:
                        st.error(f"❌ {inbox_res.get('error','UID nahi mila')}")

        
        with tab2:
            running = st.session_state.automation_state.running
            status_color = "#00b894" if running else "#d63031"
            status_text  = "🟢 Running" if running else "🔴 Stopped"
            dot_color = "#00ff88" if running else "#ff4757"
            dot_anim  = "pulse_green" if running else "pulse_red"
            st.markdown(f"""
            <style>
            @keyframes pulse_green {{
                0%,100% {{ box-shadow:0 0 0 0 rgba(0,255,136,0.7); }}
                50%      {{ box-shadow:0 0 0 8px rgba(0,255,136,0); }}
            }}
            @keyframes pulse_red {{
                0%,100% {{ box-shadow:0 0 0 0 rgba(255,71,87,0.7); }}
                50%      {{ box-shadow:0 0 0 8px rgba(255,71,87,0); }}
            }}
            </style>
            <div style="background:linear-gradient(135deg,#6c5ce7,#a29bfe,#fd79a8);
                        border-radius:16px;padding:16px 22px;margin-bottom:20px;
                        box-shadow:0 6px 24px rgba(108,92,231,0.5);
                        display:flex;align-items:center;justify-content:space-between;">
                <div style="color:#fff;font-size:1.25rem;font-weight:900;
                            letter-spacing:0.5px;text-shadow:0 2px 8px rgba(0,0,0,0.3);">
                    🚀 Automation
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="width:14px;height:14px;border-radius:50%;
                                background:{dot_color};
                                animation:{dot_anim} 1.4s ease-in-out infinite;"></div>
                    <span style="color:#fff;font-weight:700;font-size:0.95rem;
                                 background:rgba(0,0,0,0.2);border-radius:20px;
                                 padding:4px 14px;">{status_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            card2_cls = "metric-card-2r" if running else "metric-card-2s"
            bg2       = "linear-gradient(135deg,#00b894,#55efc4)" if running else "linear-gradient(135deg,#d63031,#ff7675)"
            tc2       = "#003d35" if running else "#fff"

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a0533,#2d1b69);
                        border-radius:16px;padding:18px 20px;margin-bottom:20px;
                        border:1.5px solid #6c5ce7;
                        box-shadow:0 6px 28px rgba(108,92,231,0.35);">
                <div style="display:flex;gap:12px;margin-bottom:12px;">
                    <div class="metric-card metric-card-1" style="flex:1;
                        background:linear-gradient(135deg,#00b894,#00cec9,#55efc4);">
                        <div style="color:#003d35;font-size:0.75rem;font-weight:800;
                                    letter-spacing:0.5px;margin-bottom:6px;">📨 Messages Sent</div>
                        <div style="color:#003d35;font-size:2rem;font-weight:900;line-height:1;">
                            {st.session_state.automation_state.message_count}
                        </div>
                    </div>
                    <div class="metric-card metric-card-3" style="flex:1;
                        background:linear-gradient(135deg,#4b0082,#6c5ce7,#a29bfe);">
                        <div style="color:#fff;font-size:0.75rem;font-weight:800;
                                    letter-spacing:0.5px;margin-bottom:6px;">📊 Total Logs</div>
                        <div style="color:#fff;font-size:2rem;font-weight:900;line-height:1;">
                            {len(st.session_state.automation_state.logs)}
                        </div>
                    </div>
                </div>
                <div class="metric-card {card2_cls}" style="width:100%;box-sizing:border-box;background:{bg2};">
                    <div style="color:{tc2};font-size:0.75rem;font-weight:800;
                                letter-spacing:0.5px;margin-bottom:6px;">⚡ Status</div>
                    <div style="color:{tc2};font-size:1.2rem;font-weight:900;line-height:1;">
                        {status_text}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start E2ee", disabled=running, use_container_width=True):
                    current_config = db.get_user_config(st.session_state.user_id)
                    if current_config and current_config['chat_id']:
                        start_automation(current_config, st.session_state.user_id)
                        st.rerun()
                    else:
                        st.error("❌ Please configure Chat ID first!")
            with col2:
                if st.button("⏹️ Stop E2ee", disabled=not running, use_container_width=True):
                    stop_automation(st.session_state.user_id)
                    st.rerun()

            # ── Auto-Refresh Toggle ─────────────────────────────────────────
            col_logs_hdr, col_refresh = st.columns([3, 1])
            with col_logs_hdr:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#1a0533,#2d1b69);border-radius:12px;
                            padding:10px 16px;margin:16px 0 8px;border:1px solid #6c5ce7;">
                    <span style="color:#a29bfe;font-weight:800;font-size:1rem;">📊 Live Logs</span>
                </div>
                """, unsafe_allow_html=True)
            with col_refresh:
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                auto_refresh = st.toggle("🔄 Auto", value=True, key="auto_refresh_toggle",
                                         help="Har 3 sec mein logs khud update honge")

            if st.session_state.automation_state.logs:
                logs_html = '<div class="log-container">'
                for log in st.session_state.automation_state.logs[-60:]:
                    logs_html += f'<div>{log}</div>'
                logs_html += '</div>'
                st.markdown(logs_html, unsafe_allow_html=True)
            else:
                st.info("No logs yet. Start automation to see logs here.")

            st.markdown('</div>', unsafe_allow_html=True)

            if auto_refresh and st.session_state.automation_state.running:
                time.sleep(3)
                st.rerun()
            elif not st.session_state.automation_state.running:
                pass  # stopped — no auto rerun
            else:
                # Auto-refresh off but running — manual refresh button
                if st.button("🔃 Refresh Logs", use_container_width=True, key="manual_refresh_logs"):
                    st.rerun()

st.markdown('<div class="footer-box">🔒 TERMS OF SERVICE | 🔗 FACEBOOK SECURE | 🔐 ©2025-2026 RIGHT RESERVED 💙 CREATED BY | 🩶 [R9J 🩷 TH4K9R]</div>', unsafe_allow_html=True)
