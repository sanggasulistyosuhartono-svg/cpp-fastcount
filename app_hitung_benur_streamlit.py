import cv2
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
HEADER_LOGO = Path("logo_header.png")

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
    padding-top: 1rem;
    max-width: 100%;
}

.stApp {
    background: linear-gradient(135deg, #f5fbff 0%, #ffffff 45%, #eafffb 100%);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0646b8 0%, #078ed1 55%, #10bfae 100%);
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p {
    color: white !important;
}

.logo-card {
    background: white;
    padding: 18px;
    border-radius: 22px;
    box-shadow: 0px 8px 24px rgba(0,0,0,0.12);
    margin-bottom: 18px;
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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="logo-card">', unsafe_allow_html=True)

if HEADER_LOGO.exists():
    st.image(str(HEADER_LOGO), use_container_width=True)
else:
    st.title("💧 AquaCount")

st.markdown('</div>', unsafe_allow_html=True)

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
        st.subheader("📷 Foto Asli")
        st.image(image_rgb, use_container_width=True)

    with col2:
        st.subheader("🎯 Hasil Deteksi")
        st.image(result_img, use_container_width=True)

    with col3:
        st.subheader("🧠 Mask")
        st.image(thresh_img, use_container_width=True)

    with col4:
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

        if st.button("💾 Simpan Data"):
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

else:
    st.markdown("""
    <div class="mini-card">
        <b>📌 Cara Pakai AquaCount:</b><br>
        1. Isi data sampling di sidebar.<br>
        2. Upload foto benur.<br>
        3. Cek hasil deteksi.<br>
        4. Koreksi manual bila perlu.<br>
        5. Klik Simpan Data.
    </div>
    """, unsafe_allow_html=True)
