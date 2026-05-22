import cv2
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
from pathlib import Path
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

DATA_FILE = Path("hasil_hitung_benur.csv")
SPREADSHEET_ID = "13XAwI8y9F6yox2yFdXWQ8kn80ep9E-uUA-xn8WI7b5Y"


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
        str(row["tanggal"]),
        row["unit"],
        row["batch"],
        row["tank"],
        row["umur_pl"],
        row["operator"],
        int(row["hasil_deteksi"]),
        int(row["hasil_koreksi"]),
        row["catatan"],
    ])


st.set_page_config(
    page_title="CPP FastCount",
    page_icon="🦐",
    layout="wide"
)

st.title("🦐 CPP FastCount")
st.write("Upload foto benur untuk menghitung estimasi jumlah benur.")

with st.sidebar:
    st.header("Data Sampling")
    unit = st.text_input("Unit Hatchery", "Makassar")
    batch = st.text_input("Batch")
    tank = st.text_input("Nomor Tank")
    umur_pl = st.text_input("Umur PL", "PL10")
    operator = st.text_input("Operator")

    st.header("Parameter Deteksi")
    threshold = st.slider("Threshold", 0, 255, 120)
    min_area = st.slider("Min Area", 1, 500, 15)
    max_area = st.slider("Max Area", 10, 5000, 700)
    blur = st.slider("Blur", 1, 21, 5, step=2)

uploaded_file = st.file_uploader(
    "Upload Foto Benur",
    type=["jpg", "jpeg", "png"]
)


def detect_benur(image_rgb):
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

            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)

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


if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    image_rgb = np.array(image)

    result_img, thresh_img, count = detect_benur(image_rgb)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Foto Asli")
        st.image(image_rgb, use_container_width=True)

    with col2:
        st.subheader("Hasil Deteksi")
        st.image(result_img, use_container_width=True)

    st.subheader("Mask Deteksi")
    st.image(thresh_img, use_container_width=True)

    st.metric("Estimasi Jumlah Benur", count)

    koreksi = st.number_input(
        "Koreksi Manual",
        min_value=0,
        value=int(count)
    )

    catatan = st.text_area("Catatan")

    if st.button("Simpan Hasil"):
        row = {
            "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "unit": unit,
            "batch": batch,
            "tank": tank,
            "umur_pl": umur_pl,
            "operator": operator,
            "hasil_deteksi": count,
            "hasil_koreksi": koreksi,
            "catatan": catatan
        }

        if DATA_FILE.exists():
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        df.to_csv(DATA_FILE, index=False)

        try:
            save_to_google_sheet(row)
            st.success("Data berhasil disimpan ke Google Sheets")
        except Exception as e:
            st.error("Data gagal disimpan ke Google Sheets")
            st.exception(e)
