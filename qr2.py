import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import pandas as pd
import cv2

# 1D barcode / QR
from pyzbar.pyzbar import decode as zbar_decode

# Data Matrix
from pylibdmtx.pylibdmtx import decode as dmtx_decode

st.set_page_config(page_title="Label / QR / DataMatrix Scanner", layout="wide")
st.title("Label Scanner")
st.write("Scans Data Matrix, QR, and Barcode from label images.")

def preprocess_image(pil_img):
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    versions = []

    # original gray
    versions.append(("gray", gray))

    # sharpen
    sharp = cv2.GaussianBlur(gray, (0, 0), 3)
    sharp = cv2.addWeighted(gray, 1.5, sharp, -0.5, 0)
    versions.append(("sharp", sharp))

    # threshold
    _, th1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    versions.append(("otsu", th1))

    # adaptive threshold
    th2 = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    versions.append(("adaptive", th2))

    return versions


def rotate_image(img, angle):
    if angle == 0:
        return img
    if angle == 90:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if angle == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    if angle == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


def scan_all_codes(pil_img):
    results = []
    seen = set()

    processed_versions = preprocess_image(pil_img)

    for version_name, base_img in processed_versions:
        for angle in [0, 90, 180, 270]:
            img = rotate_image(base_img, angle)

            # ---- Data Matrix scan ----
            try:
                dmtx_res = dmtx_decode(img)
                for r in dmtx_res:
                    data = r.data.decode("utf-8", errors="ignore").strip()
                    key = ("DATAMATRIX", data)
                    if data and key not in seen:
                        seen.add(key)
                        results.append({
                            "type": "DATAMATRIX",
                            "data": data,
                            "version": version_name,
                            "angle": angle
                        })
            except Exception:
                pass

            # ---- Barcode / QR scan ----
            try:
                zbar_res = zbar_decode(img)
                for r in zbar_res:
                    data = r.data.decode("utf-8", errors="ignore").strip()
                    code_type = r.type
                    key = (code_type, data)
                    if data and key not in seen:
                        seen.add(key)
                        results.append({
                            "type": code_type,
                            "data": data,
                            "version": version_name,
                            "angle": angle
                        })
            except Exception:
                pass

    return results


def draw_boxes(pil_img):
    """
    Optional visual helper using pyzbar only for 1D barcode / QR.
    Data Matrix bounding boxes are not drawn here to keep code stable.
    """
    img_rgb = np.array(pil_img.convert("RGB"))
    draw = ImageDraw.Draw(pil_img)

    try:
        for angle in [0, 90, 180, 270]:
            rotated = rotate_image(img_rgb, angle)
            decoded = zbar_decode(rotated)

            if decoded:
                for obj in decoded:
                    rect = obj.rect
                    x, y, w, h = rect.left, rect.top, rect.width, rect.height
                    draw.rectangle((x, y, x + w, y + h), outline="green", width=4)
                    label = f"{obj.type}: {obj.data.decode('utf-8', errors='ignore')}"
                    draw.text((x, max(0, y - 20)), label, fill="green")
                break
    except Exception:
        pass

    return pil_img


mode = st.radio("Input Source", ["Upload Image", "Camera"])

image = None

if mode == "Upload Image":
    uploaded = st.file_uploader("Upload label image", type=["png", "jpg", "jpeg"])
    if uploaded:
        image = Image.open(uploaded)
else:
    cam = st.camera_input("Take label photo")
    if cam:
        image = Image.open(cam)

if image:
    st.subheader("Original Image")
    st.image(image, use_container_width=True)

    if st.button("Scan Label"):
        with st.spinner("Scanning..."):
            results = scan_all_codes(image.copy())
            marked = draw_boxes(image.copy())

        st.subheader("Scanned Preview")
        st.image(marked, use_container_width=True)

        if results:
            st.success(f"Detected {len(results)} code(s)")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)

            st.subheader("Decoded Values")
            for i, row in enumerate(results, start=1):
                st.write(f"**{i}. Type:** {row['type']}")
                st.code(row["data"])
                st.caption(f"Preprocess: {row['version']} | Rotation: {row['angle']}°")
        else:
            st.warning("No Data Matrix / barcode / QR detected.")
            st.info("Try a clearer, cropped, brighter image with the code area closer.")
