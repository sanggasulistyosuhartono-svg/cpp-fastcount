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
DATA_FILE = Path("hasil_hitung_benur.csv")
LOGO_FILE = Path("logo_cp.png")


def image_to_base64(image_path):
    if image_path.exists():
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
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
        row["batch"],
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

    _, thresh = cv2.threshold(
        gray,
        threshold,
        255,
        cv2.THRESH_BINARY_INV
    )

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

            cv2.rectangle(
                result,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                result,
                str(count),
                (x, max(y - 5, 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                1
            )

    return result, thresh, count


st.set_page_config(
    page_title="CPP FastCount",
    page_icon="🦐",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f7fff9 0%, #ffffff 45%, #fff8e6 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #063b22 0%, #0b5d34 55%, #0f7a43 100%);
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p {
        color: white !important;
    }

    .main-header {
        background: linear-gradient(90deg, #063b22, #0b5d34, #157347);
        padding: 32px;
        border-radius: 26px;
        color: white;
        box-shadow: 0px 10px 28px rgba(0,0,0,0.18);
        margin-bottom: 25px;
        border-bottom: 7px solid #d4af37;
    }

    .main-title {
        font-size: 52px;
        font-weight: 900;
        margin-bottom: 6px;
        color: #ffffff;
        letter-spacing: 0.5px;
    }

    .subtitle {
        font-size: 19px;
        color: #fff4cc;
        font-weight: 600;
    }

    .section-card {
        background: white;
        padding: 22px;
        border-radius: 18px;
        box-shadow: 0px 5px 18px rgba(0,0,0,0.07);
        margin-bottom: 22px;
        border-left: 7px solid #d4af37;
    }

    .success-box {
        background: #e8f7ef;
        border-left: 8px solid #0f8a45;
        padding: 18px;
        border-radius: 14px;
        color: #0b4d2b;
        font-weight: 800;
        font-size: 18px;
    }

    .info-box {
        background: #fff8e6;
        border-left: 8px solid #d4af37;
        padding: 16px;
        border-radius: 14px;
        color: #4a3a00;
        font-weight: 600;
        margin-bottom: 18px;
    }

    .stButton > button {
        background-color: #0f8a45;
        color: white;
        border-radius: 12px;
        border: none;
        padding: 12px 28px;
        font-size: 18px;
        font-weight: bold;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: #0b6d36;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

logo_base64 = image_to_base64(LOGO_FILE)

if logo_base64:
    st.markdown(f"""
    <div class="main-header">
        <div style="display:flex; align-items:center; gap:30px;">
            <img src="data:image/png;base64,{logo_base64}" 
                 style="
                    width:145px;
                    background:white;
                    padding:12px;
                    border-radius:24px;
                    box-shadow:0 10px 24px rgba(0,0,0,0.22);
                 ">
            <div>
                <div class="main-title">CPP FastCount</div>
                <div class="subtitle">
                    Support by Team Operation V.01 (Sangga)
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <div class="main-title">🦐 CPP FastCount</div>
        <div class="subtitle">
            Support by Team Operation V.01 (Sangga)
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="section-card">
    <b>📌 Fungsi Aplikasi:</b><br>
    Upload foto benur → deteksi otomatis → koreksi manual → simpan hasil ke Google Sheets.
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("📋 Data Sampling")
    unit = st.text_input("Unit Hatchery", "Makassar")
    batch = st.text_input("Batch")
    tank = st.text_input("Nomor Tank")
    umur_pl = st.text_input("Umur PL", "PL10")
    operator = st.text_input("Operator")

    st.header("⚙️ Parameter Deteksi")
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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📷 Foto Asli")
        st.image(image_rgb, use_container_width=True)

    with col2:
        st.subheader("🎯 Hasil Deteksi")
        st.image(result_img, use_container_width=True)

    with col3:
        st.subheader("🧠 Mask Deteksi")
        st.image(thresh_img, use_container_width=True)

    st.markdown(f"""
    <div class="info-box">
        📊 Estimasi Jumlah Benur: <span style="font-size:30px; color:#0b5d34;">{count}</span>
    </div>
    """, unsafe_allow_html=True)

    koreksi = st.number_input(
        "Koreksi Manual",
        min_value=0,
        value=int(count)
    )

    catatan = st.text_area("Catatan")

    if st.button("💾 Simpan Hasil"):
        row = {
            "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "unit": unit,
            "batch": batch,
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
            ✅ Data berhasil disimpan ke Google Sheets
        </div>
        """, unsafe_allow_html=True)
