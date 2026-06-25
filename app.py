import streamlit as st
import pandas as pd
from google import genai
import datetime
import os
import json
import random
import plotly.express as px

# --- CẤU HÌNH API HỆ THỐNG PHÂN TÍCH (SỬ DỤNG GEMINI 2.5 FLASH) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "KEY_MẶC_ĐỊNH_NẾU_CHẠY_LOCAL") 
client = genai.Client(api_key=GEMINI_API_KEY)

# --- QUẢN LÝ FILE DỮ LIỆU ---
VOCAB_FILE = "my_spaced_words.json"
USER_FILE = "users_db.json"

def load_vocab_data():
    if os.path.exists(VOCAB_FILE):
        with open(VOCAB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_vocab_data(data):
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

if "vocab_db" not in st.session_state:
    st.session_state.vocab_db = load_vocab_data()

# --- HỆ THỐNG CẤP BẬC GUNBOUND (ĐỊNH MỨC ĐIỂM GP) ---
def get_gunbound_rank(score):
    if score >= 500: return "💎 Trượng Kim Cương (SL 45)"
    elif score >= 400: return "👑 Trượng Ruby (SL 75)"
    elif score >= 300: return "🔮 Trượng Sapphire (SL 115)"
    elif score >= 220: return "🔱 Rìu Vàng Đôi"
    elif score >= 160: return "🪓 Rìu Vàng Hai Cạnh"
    elif score >= 110: return "🪵 Rìu Bạc Hai Cạnh"
    elif score >= 70:  return "⚔️ Rìu Sắt Đôi"
    elif score >= 40:  return "🔨 Búa Đá Đôi"
    elif score >= 15:  return "🪵 Búa Gỗ"
    else:              return "🐥 Gà Con"

def calculate_user_score(username, db):
    score = 0
    for v in db.values():
        if v.get("user") == username:
            score += int(v.get("box_level", 1))
    return score

# --- TỪ ĐIỂN NGÔN NGỮ GIAO DIỆN ---
LANG_DICT = {
    "Tiếng Việt": {
        "auth_title": "🔐 HỆ THỐNG XÁC THỰC THÀNH VIÊN",
        "login": "🔒 Đăng nhập",
        "register": "📝 Đăng ký tài khoản",
        "username": "Tên tài khoản:",
        "password": "Mật khẩu:",
        "confirm_pass": "Xác nhận mật khẩu:",
        "btn_login": "Xác nhận Đăng nhập",
        "btn_reg": "Đăng ký ngay",
        "logout": "Đăng xuất tài khoản",
        "tab_add": "📥 Trích xuất từ vựng mới",
        "tab_review": "🧠 Ôn tập dữ liệu ngắt quãng",
        "tab_dashboard": "📊 Trung tâm Chỉ huy",
        "tab_guide": "📖 Cẩm nang vận hành",
        "url_label": "Nhập liên kết bài viết nguồn (URL):",
        "btn_analyze": "Kích hoạt thuật toán trích xuất tự động",
        "my_vocab": "📋 Danh mục dữ liệu vựng ngữ",
        "no_vocab": "Cơ sở dữ liệu tài khoản trống cho ngôn ngữ này.",
        "review_today": "Lịch trình kiểm tra hôm nay",
        "review_done": "🎉 Xuất sắc! Bạn đã hoàn thành toàn bộ lịch trình kiểm tra của ngôn ngữ này.",
        "review_count": "Hệ thống ghi nhận {} bản ghi cần kiểm tra hôm nay.",
        "btn_forget": "🔴 CHƯA THUỘC (Đặt lại Hộp 1)",
        "btn_remember": "🟢 ĐÃ THUỘC (Chuyển Hộp tiếp theo)",
    },
    "English": {
        "auth_title": "🔐 MEMBER AUTHENTICATION SYSTEM",
        "login": "🔒 Login",
        "register": "📝 Register",
        "username": "Username:",
        "password": "Password:",
        "confirm_pass": "Confirm Password:",
        "btn_login": "Login",
        "btn_reg": "Register Now",
        "logout": "Logout Account",
        "tab_add": "📥 Extract Vocabulary",
        "tab_review": "🧠 Spaced Repetition Review",
        "tab_dashboard": "📊 Command Dashboard",
        "tab_guide": "📖 User Guide",
        "url_label": "Enter Source Article URL:",
        "btn_analyze": "Execute Automated Extraction Algorithm",
        "my_vocab": "📋 Vocabulary Database",
        "no_vocab": "Database is empty for this language.",
        "review_today": "Today's Review Schedule",
        "review_done": "🎉 Excellent! You have completed all reviews for this language today.",
        "review_count": "System detected {} records for review today.",
        "btn_forget": "🔴 FORGOT (Reset to Box 1)",
        "btn_remember": "🟢 REMEMBER (Advance to Next Box)",
    }
}

if "native_lang" not in st.session_state:
    st.session_state.native_lang = "Tiếng Việt"
if "target_lang" not in st.session_state:
    st.session_state.target_lang = "English (Tiếng Anh)"

T = LANG_DICT[st.session_state.native_lang]

def Auth_System():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None

    if st.session_state.authenticated:
        return True

    st.title(T["auth_title"])
    st.session_state.native_lang = st.selectbox("🌐 Ngôn ngữ hệ thống (System Language):", ["Tiếng Việt", "English"])
    
    tab_login, tab_register = st.tabs([T["login"], T["register"]])
    users_db = load_users()

    with tab_login:
        login_user = st.text_input(T["username"], key="login_username").strip()
        login_pass = st.text_input(T["password"], type="password", key="login_password").strip()
        if st.button(T["btn_login"]):
            if login_user in users_db and users_db[login_user] == login_pass:
                st.session_state.authenticated = True
                st.session_state.current_user = login_user
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password!")

    with tab_register:
        reg_user = st.text_input(T["username"], key="reg_username").strip()
        reg_pass = st.text_input(T["password"], type="password", key="reg_password").strip()
        reg_pass_confirm = st.text_input(T["confirm_pass"], type="password", key="reg_password_confirm").strip()
        if st.button(T["btn_reg"]):
            if not reg_user or not reg_pass:
                st.error("❌ Please fill all fields!")
            elif reg_user in users_db:
                st.error("❌ Username already exists!")
            elif reg_pass != reg_pass_confirm:
                st.error("❌ Passwords do not match!")
            else:
                users_db[reg_user] = reg_pass
                save_users(users_db)
                st.success("🎉 Registered successfully! Please go to Login tab.")
    return False

if not Auth_System():
    st.stop()

# --- GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="My Spaced Words System", layout="wide")

user_gp = calculate_user_score(st.session_state.current_user, st.session_state.vocab_db)
user_rank = get_gunbound_rank(user_gp)

with st.sidebar:
    st.header("⚙️ Thiết lập cấu trúc")
    st.session_state.native_lang = st.selectbox("🌐 Ngôn ngữ mẹ đẻ:", ["Tiếng Việt", "English"], index=0 if st.session_state.native_lang == "Tiếng Việt" else 1)
    st.session_state.target_lang = st.selectbox("🎯 Mục tiêu ngôn ngữ học:", ["English (Tiếng Anh)", "Chinese (Tiếng Trung)", "Japanese (Tiếng Nhật)"])
    st.write("---")
    
    st.subheader("🎮 Chỉ số năng lực")
    st.write(f"👤 Tài khoản: **{st.session_state.current_user}**")
    st.info(f"🏆 Cấp bậc: **{user_rank}**")
    st.metric(label="✨ Điểm tích lũy hệ thống (GP)", value=f"{user_gp} đ")
    
    st.write("---")
    if st.button(T["logout"]):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

T = LANG_DICT[st.session_state.native_lang]

# Thứ tự cấu trúc Tab đồng bộ hoàn toàn
tab1, tab2, tab4, tab3 = st.tabs([T["tab_add"], T["tab_review"], T["tab_dashboard"], T["tab_guide"]])

def clean_html_for_radio(text):
    import re
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text.replace("**", "")

# --- CẬP NHẬT: HÀM PHÂN TÍCH AN TOÀN, CHỐNG LỖI ĐỊNH DẠNG JSON VÀ KHÓA BOT ---
def analyze_article_with_gemini(url):
    prompt = f"""
    Hãy phân tích văn bản từ liên kết: {url}.
    Mục tiêu: Người đọc có ngôn ngữ nền là '{st.session_state.native_lang}' và đang nghiên cứu '{st.session_state.target_lang}'.
    Lọc ra đúng 5 từ khóa cốt lõi thuộc hệ ngôn ngữ '{st.session_state.target_lang}' trong bài viết.
    Trả về cấu trúc mảng JSON thuần túy (không bọc trong khối markdown ```json), gồm các đối tượng có cấu trúc trường bắt buộc:
    - "word": Từ vựng
    - "meaning": Định nghĩa bằng ngôn ngữ '{st.session_state.native_lang}'. Định dạng bắt buộc: Từ dịch nghĩa chính yếu nhất phải được bọc trong thẻ html này: <span style='color:green'>**từ_chính**</span>. Các thành phần diễn giải ngữ cảnh mở rộng (nếu có) viết chữ thường bên ngoài thẻ.
    - "context": Câu văn mẫu trích từ bài viết hoặc tương đương sử dụng hệ chữ '{st.session_state.target_lang}'.
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        text_data = response.text.strip()
        
        if text_data.startswith("```"):
            text_data = text_data.replace("```json", "").replace("```", "").strip()
            
        if not text_data:
