import streamlit as st
import pandas as pd
from google import genai
import datetime
import os
import json
import random
import plotly.express as px

# --- CẤU HÌNH API HỆ THỐNG PHÂN TÍCH ---
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

# Đã chuẩn hóa thứ tự biến nhận diện tab trùng với thứ tự mảng tiêu đề
tab1, tab2, tab4, tab3 = st.tabs([T["tab_add"], T["tab_review"], T["tab_dashboard"], T["tab_guide"]])

def clean_html_for_radio(text):
    import re
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text.replace("**", "")

def analyze_article_with_gemini(url):
    prompt = f"""
    Hãy phân tích văn bản từ liên kết: {url}.
    Mục tiêu: Người đọc có ngôn ngữ nền là '{st.session_state.native_lang}' và đang nghiên cứu '{st.session_state.target_lang}'.
    Lọc ra đúng 5 từ khóa cốt lõi thuộc hệ ngôn ngữ '{st.session_state.target_lang}' trong bài viết.
    Trả về cấu trúc mảng JSON thuần túy (không bọc trong khối markdown), gồm các đối tượng có cấu trúc trường bắt buộc:
    - "word": Từ vựng
    - "meaning": Định nghĩa bằng ngôn ngữ '{st.session_state.native_lang}'. Định dạng bắt buộc: Từ dịch nghĩa chính yếu nhất phải được bọc trong thẻ html này: <span style='color:green'>**từ_chính**</span>. Các thành phần diễn giải ngữ cảnh mở rộng (nếu có) viết chữ thường bên ngoài thẻ.
    - "context": Câu văn mẫu trích từ bài viết hoặc tương đương sử dụng hệ chữ '{st.session_state.target_lang}'.
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        text_data = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text_data)
    except Exception as e:
        st.error(f"Xử lý thất bại: {e}")
        return None

# --- TAB 1: TRÍCH XUẤT TỰ ĐỘNG ---
with tab1:
    st.header(T["url_label"])
    url_input = st.text_input("", placeholder="https://...", key="url_text_field")
    
    if st.button(T["btn_analyze"]):
        if url_input:
            with st.spinner("Đang chạy phân tích cú pháp dữ liệu bài viết..."):
                words_list = analyze_article_with_gemini(url_input)
                if words_list:
                    st.success("Hệ thống trích xuất và đồng bộ dữ liệu thành công!")
                    today = str(datetime.date.today())
                    for item in words_list:
                        w_key = f"{st.session_state.current_user}_{st.session_state.target_lang}_{item['word'].lower()}"
                        if w_key not in st.session_state.vocab_db:
                            st.session_state.vocab_db[w_key] = {
                                "user": st.session_state.current_user,
                                "target_lang": st.session_state.target_lang,
                                "word": item['word'],
                                "meaning": item['meaning'],
                                "context": item['context'],
                                "box_level": 1,
                                "next_review": today
                            }
                    save_vocab_data(st.session_state.vocab_db)
                    st.rerun()

    st.subheader(T["my_vocab"] + f" ({st.session_state.target_lang})")
    user_words = [
        v for v in st.session_state.vocab_db.values() 
        if v.get("user") == st.session_state.current_user and v.get("target_lang") == st.session_state.target_lang
    ]
    if user_words:
        df = pd.DataFrame(user_words)
        st.write(df[["word", "meaning", "box_level", "next_review"]].to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info(T["no_vocab"])

# --- TAB 2: ÔN TẬP NGẮT QUÃNG TRẮC NGHIỆM ---
with tab2:
    st.header(T["review_today"] + f" ({st.session_state.target_lang})")
    today_str = str(datetime.date.today())
    
    all_user_words = [
        v for v in st.session_state.vocab_db.values() 
        if v.get("user") == st.session_state.current_user and v.get("target_lang") == st.session_state.target_lang
    ]
    
    review_list = [v for v in all_user_words if v["next_review"] <= today_str]
    
    if not review_list:
        st.success(T["review_done"])
    else:
        st.warning(T["review_count"].format(len(review_list)))
        current_word = review_list[0]
        w_key = f"{st.session_state.current_user}_{st.session_state.target_lang}_{current_word['word'].lower()}"
        
        st.info(f"💡 **Ngữ cảnh thực tế:** {current_word['context']}")
        st.markdown(f"### Thuật ngữ cần định nghĩa: `{current_word['word']}`")
        st.write("---")
        
        if "quiz_word" not in st.session_state or st.session_state.quiz_word != current_word['word']:
            st.session_state.quiz_word = current_word['word']
            st.session_state.answered = False
            st.session_state.submit_clicked = False
            
            correct_meaning = current_word['meaning']
            wrong_meanings = [w['meaning'] for w in all_user_words if w['word'] != current_word['word']]
            wrong_meanings = list(set(wrong_meanings))
            wrong_options = random.sample(wrong_meanings, min(len(wrong_meanings), 3))
            
            options = wrong_options + [correct_meaning]
            random.shuffle(options)
            st.session_state.quiz_options = options

        display_options_map = {clean_html_for_radio(opt): opt for opt in st.session_state.quiz_options}
        
        chosen_clean = st.radio(
            "Lựa chọn phương án khớp nghĩa chính xác nhất:", 
            list(display_options_map.keys()), 
            index=0,
            disabled=st.session_state.submit_clicked
        )
        
        selected_origin_meaning = display_options_map[chosen_clean]

        if st.button("Xác nhận kiểm tra phương án", disabled=st.session_state.submit_clicked):
            st.session_state.submit_clicked = True
            if selected_origin_meaning == current_word['meaning']:
                st.session_state.answered = True
            else:
                st.session_state.answered = False

        if st.session_state.submit_clicked:
            if st.session_state.answered:
                st.success("🎉 CHÍNH XÁC!")
                st.write("Định nghĩa gốc của hệ thống: ", unsafe_allow_html=True)
                st.write(current_word['meaning'], unsafe_allow_html=True)
                
                if st.button("🟢 Tiếp tục lịch trình (Tăng mức độ lưu trữ)"):
                    current_level = current_word['box_level']
                    next_level = min(current_level + 1, 3)
                    days_gap = 1 if next_level == 1 else (3 if next_level == 2 else 7)
                    
                    st.session_state.vocab_db[w_key]['box_level'] = next_level
                    st.session_state.vocab_db[w_key]['next_review'] = str(datetime.date.today() + datetime.timedelta(days=days_gap))
                    save_vocab_data(st.session_state.vocab_db)
                    
                    if "quiz_word" in st.session_state:
                        del st.session_state.quiz_word
                    st.rerun()
            else:
                st.error("❌ PHƯƠNG ÁN CHƯA CHÍNH XÁC!")
                st.write("Định nghĩa gốc đúng của hệ thống: ", unsafe_allow_html=True)
                st.write(current_word['meaning'], unsafe_allow_html=True)
                
                if st.button("🔴 Tiếp tục lịch trình (Đặt lại chu kỳ cơ bản)"):
                    st.session_state.vocab_db[w_key]['box_level'] = 1
                    st.session_state.vocab_db[w_key]['next_review'] = str(datetime.date.today() + datetime.timedelta(days=1))
                    save_vocab_data(st.session_state.vocab_db)
                    
                    if "quiz_word" in st.session_state:
                        del st.session_state.quiz_word
                    st.rerun()

# --- TAB 4: TRUNG TÂM CHỈ HUY (DASHBOARD) ---
with tab4:
    st.header("📊 Trung tâm Chỉ huy Bộ nhớ")
    
    user_all_data = [v for v in st.session_state.vocab_db.values() if v.get("user") == st.session_state.current_user]
    
    if not user_all_data:
        st.info("Chưa có đủ dữ liệu để phân tích xu hướng. Hãy trích xuất thêm từ vựng!")
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🧠 Tỷ lệ phân bổ Hộp trí nhớ")
            df_box = pd.DataFrame(user_all_data)
            df_counts = df_box['box_level'].value_counts().reset_index()
            df_counts.columns = ['Hộp lưu trữ', 'Số lượng từ']
            df_counts['Hộp lưu trữ'] = df_counts['Hộp lưu trữ'].apply(lambda x: f"Hộp {x}")
            
            fig_pie = px.pie(
                df_counts, 
                values='Số lượng từ', 
                names='Hộp lưu trữ', 
                color_discrete_sequence=px.colors.sequential.Plasma,
                hole=0.3
            )
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            st.subheader("🔥 Ma trận Lịch nhiệt học tập (30 ngày gần đây)")
            
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=29)
            date_range = [start_date + datetime.timedelta(days=i) for i in range(30)]
            
            date_counts = {str(d): 0 for d in date_range}
            for v in user_all_data:
                nr_date = v.get("next_review")
                if nr_date in date_counts:
                    date_counts[nr_date] += 1
            
            grid_data = list(date_counts.items())
            
            st.caption("Mức độ dày đặc của từ vựng phân phối theo ngày (Màu đậm hơn = Nhiều từ cần xử lý hơn):")
            
            # --- FIX LỖI TẠI ĐÂY: Chuẩn hóa Container Grid và xử lý nối chuỗi HTML an toàn ---
            html_grid = "<div style='display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; max-width: 500px;'>"
            for d_str, count in grid_data:
                if count == 0:
                    bg_color = "#ebedf0"
                    text_color = "#000000"
                elif count <= 2:
                    bg_color = "#9be9a8"
                    text_color = "#000000"
                elif count <= 4:
                    bg_color = "#40c463"
                    text_color = "#ffffff"
                else:
                    bg_color = "#216e39"
                    text_color = "#ffffff"
                
                day_display = d_str.split("-")[2]
                
                # Tạo chuỗi HTML con cho từng ô một cách mạch lạc
                cell_html = (
                    f"<div style='background-color: {bg_color}; color: {text_color}; padding: 12px; "
                    f"text-align: center; border-radius: 4px; font-weight: bold; font-size: 14px;' title='Ngày {d_str}: {count} từ'>"
                    f"{day_display}"
                    f"<div style='font-size: 9px; font-weight: normal; opacity: 0.8;'>{count} từ</div>"
                    f"</div>"
                )
                html_grid += cell_html
                
            html_grid += "</div>"
            st.write(html_grid, unsafe_allow_html=True)
            st.write("")
            
        st.write("---")
        st.subheader("📈 Chỉ số tăng trưởng vựng ngữ")
        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng số từ đã nạp", f"{len(user_all_data)} từ")
        m2.metric("Số từ đã đạt Hộp 3 (Master)", f"{len(df_box[df_box['box_level'] == 3]) if 'box_level' in df_box.columns else 0} từ")
        m3.metric("Hiệu suất bộ nhớ trung bình", f"{round((user_gp / (len(user_all_data) * 3)) * 100, 1) if user_all_data else 0} %")




# --- TAB 3: HƯỚNG DẪN SỬ DỤNG ---
with tab3:
    st.header("📖 Hướng dẫn vận hành Cơ sở Hệ thống Ngắt quãng MyWords")
    st.markdown("""
    Chào mừng bạn đến với môi trường lưu trữ và kiểm soát vựng ngữ ứng dụng cơ chế ngắt quãng tự động hóa kết hợp thang đo kiểm chuẩn năng lực!
    
    ### 1. Quy trình vận hành cốt lõi
    * **Bước 1:** Cấu hình **Mục tiêu ngôn ngữ học** tại thanh điều khiển trái (Tiếng Anh, Tiếng Trung...).
    * **Bước 2:** Truy cập các cổng thông tin báo chí uy tín được liên kết phía dưới, sao chép (Copy) đường dẫn URL của bài viết cần nghiên cứu.
    * **Bước 3:** Tại phân hệ **Trích xuất từ vựng mới**, dán liên kết vào ô nhập liệu và chạy lệnh. Hệ thống máy chủ sẽ tự động bóc tách từ khóa, <span style='color:green'>**in đậm tô xanh**</span> nghĩa gốc chuẩn xác nhất.
    * **Bước 4:** Định kỳ truy cập phân hệ **Ôn tập dữ liệu ngắt quãng** hàng ngày để làm bài trắc nghiệm tự động kiểm chuẩn chu kỳ trí nhớ.

    ### 2. Danh sách cổng thông tin kiểm thử tiêu biểu (Bấm để lấy liên kết bài viết)
    * 📰 **[BBC News](https://www.bbc.com/news)** – Cổng tin tức quốc tế, hệ thống từ vựng chính luận chuẩn cấu trúc.
    * 📰 **[CNN International](https://edition.cnn.com)** – Tin tức thời sự cập nhật liên tục về công nghệ, đời sống xã hội.
    * 📰 **[Xinhua Net (Tân Hoa Xã)](http://www.xinhuanet.com)** – Cơ quan báo chí chính thống, từ vựng chuẩn xã hội và kinh tế thương mại.
    * 📰 **[NHK News Web Easy](https://www3.nhk.or.jp/news/easy/)** – **Nguồn ngữ liệu chuẩn tối ưu.** Văn bản được tinh giản cấu trúc sạch giúp hệ thống phân tích đạt độ chính xác tuyệt đối.

    ---

    ### 3. Thang đo kiểm chuẩn năng lực và Hệ thống cấp bậc (Gamify)
    Thuật toán tự động phân bổ bản ghi từ vựng vào các phân vùng lưu trữ (Hộp bộ nhớ - Box Level) từ 1 đến 3. Chỉ số phân vùng tỷ lệ thuận với độ bền vững thông tin trong bộ nhớ:
    * **Phân vùng Hộp 1:** Ghi nhận **1 điểm GP** (Hệ thống xếp lịch kiểm tra lại vào chu kỳ ngày kế tiếp).
    * **Phân vùng Hộp 2:** Ghi nhận **2 điểm GP** (Hệ thống ngắt quãng tự động và kiểm tra lại sau 3 ngày).
    * **Phân vùng Hộp 3:** Ghi nhận **3 điểm GP** (Độ thuộc bài sâu, hệ thống ngắt quãng kéo dài 7 ngày).
    """, unsafe_allow_html=True)
