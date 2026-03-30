import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
import cv2

from pyzbar.pyzbar import decode as zbar_decode
from pylibdmtx.pylibdmtx import decode as dmtx_decode

st.set_page_config(page_title="Delivery Label Scanner", layout="wide")
st.title("Delivery Label Scanner")

# ----------------------------
# Helpers
# ----------------------------
def prepare_image(pil_img, max_width=1200):
    img = ImageOps.exif_transpose(pil_img).convert("RGB")

    w, h = img.size
    if w > max_width:
        new_h = int(h * (max_width / w))
        img = img.resize((max_width, new_h))

    return img

def to_gray_np(pil_img):
    arr = np.array(pil_img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    return gray

def try_dmtx(img_np):
    try:
        results = dmtx_decode(img_np)
        output = []
        for r in results:
            data = r.data.decode("utf-8", errors="ignore").strip()
            if data:
                output.append({
                    "type": "DATAMATRIX",
                    "data": data
                })
        return output
    except Exception as e:
        return [{"type": "ERROR", "data": f"DMTX error: {e}"}]

def try_zbar(img_np):
    try:
        results = zbar_decode(img_np)
        output = []
        for r in results:
            data = r.data.decode("utf-8", errors="ignore").strip()
            if data:
                output.append({
                    "type": r.type,
                    "data": data
                })
        return output
    except Exception as e:
        return [{"type": "ERROR", "data": f"ZBAR error: {e}"}]

def scan_image_once(pil_img):
    img = prepare_image(pil_img)
    gray = to_gray_np(img)

    # 1) direct grayscale
    found = []

    d1 = try_dmtx(gray)
    found.extend([x for x in d1 if x["type"] != "ERROR"])

    z1 = try_zbar(gray)
    found.extend([x for x in z1 if x["type"] != "ERROR"])

    if found:
        return found, img

    # 2) rotate 90 once
    rot = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)

    d2 = try_dmtx(rot)
    found.extend([x for x in d2 if x["type"] != "ERROR"])

    z2 = try_zbar(rot)
    found.extend([x for x in z2 if x["type"] != "ERROR"])

    # dedupe
    unique = []
    seen = set()
    for x in found:
        key = (x["type"], x["data"])
        if key not in seen:
            seen.add(key)
            unique.append(x)

    return unique, img

# ----------------------------
# UI
# ----------------------------
mode = st.radio("Input Source", ["Upload Image", "Camera"])

image = None

if mode == "Upload Image":
    uploaded = st.file_uploader("Upload label image", type=["jpg", "jpeg", "png"])
    if uploaded:
        image = Image.open(uploaded)
else:
    cam = st.camera_input("Take photo")
    if cam:
        image = Image.open(cam)

if image:
    st.image(image, caption="Input Image", use_container_width=True)

    if st.button("Scan Now"):
        with st.spinner("Scanning label once..."):
            results, preview = scan_image_once(image)

        st.image(preview, caption="Processed Preview", use_container_width=True)

        if results:
            st.success(f"{len(results)} code(s) found")

            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)

            for i, r in enumerate(results, start=1):
                st.write(f"**{i}. {r['type']}**")
                st.code(r["data"])
        else:
            st.warning("No code found.")
            st.info("Try cropping only the code area and upload again.")
