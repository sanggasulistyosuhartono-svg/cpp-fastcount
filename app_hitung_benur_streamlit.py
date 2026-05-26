import cv2
import base64
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
from pathlib import Path
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "13XAwI8y9F6yox2yFdXWQ8kn80ep9E-uUA-xn8WI7b5Y"
DATA_FILE = Path("hasil_hitung_aquacount.csv")
AQUACOUNT_LOGO = Path("logo_aquacount.png")
CP_LOGO = Path("logo_cp.png")


def image_to_base64(path):
    if path.exists():
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def save_to_google_sheet(row):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )

    client = gspread.authorize(credentials)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    sheet.append_row([
        row["tanggal"],
        row["unit"],
        row["tank"],
        row["umur_pl"],
        row["operator"],
        row["hasil_deteksi"],
        row["hasil_koreksi"],
        row["catatan"],
    ])


def detect_benur(image_rgb, threshold, min_area, max_area, blur):
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (blur, blur), 0)

    _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    result = image_rgb.copy()
    count = 0

    for contour in contours:
        area = cv2.contourArea(contour)

        if min_area <= area <= max_area:
            count += 1
            x, y, w, h = cv2.boundingRect(contour)

            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 180, 120), 2)

            cv2.putText(
                result,
                str(count),
                (x, max(y - 5, 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 90, 255),
                1
            )

    return result, thresh, count


st.set_page_config(
    page_title="AquaCount",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }

    .stApp {
        background: linear-gradient(135deg, #f5fbff 0%, #ffffff 45%, #eafffb 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0646b8 0%, #078ed1 55%, #10bfae 100%);
        width: 300px !important;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p {
        color: white !important;
    }

    .header-box {
        background: linear-gradient(90deg, #0646b8, #078ed1, #10bfae);
        padding: 22px 30px;
        border-radius: 22px;
        box-shadow: 0px 8px 24px rgba(0,0,0,0.15);
        margin-bottom: 16px;
        border-bottom: 5px solid #11d3c5;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
    }

    .logo-panel {
        background: white;
        padding: 16px 24px;
        border-radius: 22px;
        box-shadow: 0px 8px 22px rgba(0,0,0,0.18);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 26px;
        min-width: 560px;
    }

    .aqua-logo {
        width: 360px;
        height: auto;
        object-fit: contain;
    }

    .cp-logo {
        width: 120px;
        height: auto;
        object-fit: contain;
    }

    .brand-title {
        font-size: 50px;
        font-weight: 900;
        color: white;
        margin-bottom: 8px;
        line-height: 1;
    }

    .brand-subtitle {
        font-size: 18px;
        color: #eafffb;
        font-weight: 800;
        letter-spacing: 1.6px;
    }

    .mini-card {
        background: white;
        padding: 12px;
        border-radius: 14px;
        box-shadow: 0px 4px 14px rgba(0,0,0,0.07);
        height: 100%;
    }

    .result-box {
        background: #eafffb;
        border-left: 7px solid #11d3c5;
        padding: 14px;
        border-radius: 14px;
        color: #0646b8;
        font-weight: 800;
        font-size: 28px;
        text-align: center;
        margin-bottom: 10px;
    }

    .success-box {
        background: #e6fff9;
        border-left: 7px solid #10bfae;
        padding: 12px;
        border-radius: 12px;
        color: #0646b8;
        font-weight: 700;
        font-size: 15px;
    }

    .stButton > button {
        background-color: #10bfae;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: #078ed1;
        color: white;
    }

    img {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


aqua_logo_b64 = image_to_base64(AQUACOUNT_LOGO)
cp_logo_b64 = image_to_base64(CP_LOGO)

aqua_logo_html = (
    f'<img class="aqua-logo" src="data:image/png;base64,{aqua_logo_b64}">'
    if aqua_logo_b64 else
    '<div style="font-size:32px;font-weight:800;color:#0646b8;">AquaCount</div>'
)

cp_logo_html = (
    f'<img class="cp-logo" src="data:image/png;base64,{cp_logo_b64}">'
    if cp_logo_b64 else
    ''
)

st.markdown(f"""
<div class="header-box">
    <div class="logo-panel">
        {aqua_logo_html}
        {cp_logo_html}
    </div>

    <div>
        <div class="brand-title">AquaCount</div>
        <div class="brand-subtitle">ACCURATE • FAST • RELIABLE • CONTINUOUS</div>
    </div>
</div>
""", unsafe_allow_html=True)


with st.sidebar:
    st.header("📋 Data Sampling")

    unit = st.text_input("Unit Hatchery", "Makassar")
    tank = st.text_input("Nomor Tank")
    umur_pl = st.text_input("Umur PL", "PL10")
    operator = st.text_input("Operator")

    st.header("⚙️ Parameter")
    threshold = st.slider("Threshold", 0, 255, 120)
    min_area = st.slider("Min Area", 1, 500, 15)
    max_area = st.slider("Max Area", 10, 5000, 700)
    blur = st.slider("Blur", 1, 21, 5, step=2)


uploaded_file = st.file_uploader(
    "📤 Upload Foto Benur",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    image_rgb = np.array(image)

    result_img, thresh_img, count = detect_benur(
        image_rgb,
        threshold,
        min_area,
        max_area,
        blur
    )

    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 0.9])

    with col1:
        st.markdown('<div class="mini-card">', unsafe_allow_html=True)
        st.subheader("📷 Foto Asli")
        st.image(image_rgb, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="mini-card">', unsafe_allow_html=True)
        st.subheader("🎯 Hasil Deteksi")
        st.image(result_img, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="mini-card">', unsafe_allow_html=True)
        st.subheader("🧠 Mask")
        st.image(thresh_img, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="mini-card">', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="result-box">
            Jumlah<br>{count}
        </div>
        """, unsafe_allow_html=True)

        koreksi = st.number_input(
            "Koreksi Manual",
            min_value=0,
            value=int(count)
        )

        catatan = st.text_area("Catatan", height=90)

        if st.button("💾 Simpan"):
            row = {
                "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "unit": unit,
                "tank": tank,
                "umur_pl": umur_pl,
                "operator": operator,
                "hasil_deteksi": int(count),
                "hasil_koreksi": int(koreksi),
                "catatan": catatan
            }

            if DATA_FILE.exists():
                df = pd.read_csv(DATA_FILE)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            else:
                df = pd.DataFrame([row])

            df.to_csv(DATA_FILE, index=False)
            save_to_google_sheet(row)

            st.markdown("""
            <div class="success-box">
                ✅ Data tersimpan ke Google Sheets
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="mini-card">
        <b>📌 Cara Pakai AquaCount:</b><br>
        1. Isi data sampling di sidebar.<br>
        2. Upload foto benur.<br>
        3. Cek hasil deteksi.<br>
        4. Koreksi manual bila perlu.<br>
        5. Klik Simpan.
    </div>
    """, unsafe_allow_html=True)
