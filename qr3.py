import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
import cv2

from pyzbar.pyzbar import decode as zbar_decode

# optional: only if pylibdmtx works in your Python 3.11 env
USE_DMTX = True
try:
    from pylibdmtx.pylibdmtx import decode as dmtx_decode
except Exception:
    USE_DMTX = False


st.set_page_config(page_title="Auto Label Crop + Scan", layout="wide")
st.title("Auto Label Crop + Scan")


# -----------------------------
# Helpers
# -----------------------------
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left
    rect[2] = pts[np.argmax(s)]   # bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    return rect


def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped


def prepare_image(pil_img, max_width=1400):
    img = ImageOps.exif_transpose(pil_img).convert("RGB")
    w, h = img.size
    if w > max_width:
        new_h = int(h * (max_width / w))
        img = img.resize((max_width, new_h))
    return img


def auto_crop_label(pil_img):
    img = np.array(prepare_image(pil_img))
    original = img.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edged = cv2.Canny(blur, 50, 150)

    kernel = np.ones((5, 5), np.uint8)
    edged = cv2.dilate(edged, kernel, iterations=1)
    edged = cv2.erode(edged, kernel, iterations=1)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_quad = None
    best_area = 0
    h, w = gray.shape

    min_area = (h * w) * 0.08

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        if len(approx) == 4 and area > best_area:
            best_quad = approx
            best_area = area

    if best_quad is not None:
        pts = best_quad.reshape(4, 2).astype("float32")
        warped = four_point_transform(original, pts)

        if warped.shape[0] > warped.shape[1]:
            warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)

        return Image.fromarray(warped), True

    # fallback: center crop if contour not found
    hh, ww = gray.shape
    x1 = int(ww * 0.10)
    x2 = int(ww * 0.90)
    y1 = int(hh * 0.18)
    y2 = int(hh * 0.82)

    crop = original[y1:y2, x1:x2]

    if crop.shape[0] > crop.shape[1]:
        crop = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)

    return Image.fromarray(crop), False


def make_variants(pil_img):
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    variants = []

    variants.append(("gray", gray))

    _, th1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("otsu", th1))

    th2 = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8
    )
    variants.append(("adaptive", th2))

    sharp = cv2.GaussianBlur(gray, (0, 0), 3)
    sharp = cv2.addWeighted(gray, 1.5, sharp, -0.5, 0)
    variants.append(("sharp", sharp))

    return variants


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


def decode_all(pil_img):
    results = []
    seen = set()

    variants = make_variants(pil_img)

    # keep attempts limited for speed
    for vname, base in variants[:3]:
        for angle in [0, 90]:
            test = rotate_image(base, angle)

            if USE_DMTX:
                try:
                    dres = dmtx_decode(test, timeout=50)
                    for r in dres:
                        data = r.data.decode("utf-8", errors="ignore").strip()
                        key = ("DATAMATRIX", data)
                        if data and key not in seen:
                            seen.add(key)
                            results.append({
                                "type": "DATAMATRIX",
                                "data": data,
                                "variant": vname,
                                "angle": angle
                            })
                except Exception:
                    pass

            try:
                zres = zbar_decode(test)
                for r in zres:
                    data = r.data.decode("utf-8", errors="ignore").strip()
                    key = (r.type, data)
                    if data and key not in seen:
                        seen.add(key)
                        results.append({
                            "type": r.type,
                            "data": data,
                            "variant": vname,
                            "angle": angle
                        })
            except Exception:
                pass

            if results:
                return results

    return results


# -----------------------------
# UI
# -----------------------------
mode = st.radio("Input Source", ["Camera", "Upload Image"])

image = None

if mode == "Camera":
    cam = st.camera_input("Take label photo")
    if cam:
        image = Image.open(cam)
else:
    uploaded = st.file_uploader("Upload label image", type=["jpg", "jpeg", "png"])
    if uploaded:
        image = Image.open(uploaded)

if image:
    st.subheader("Original Image")
    st.image(image, use_container_width=True)

    with st.spinner("Auto cropping label..."):
        cropped_label, exact_found = auto_crop_label(image)

    st.subheader("Auto Cropped Label")
    st.image(cropped_label, use_container_width=True)

    if exact_found:
        st.success("Label area detected")
    else:
        st.warning("Exact label border not found, used fallback crop")

    with st.spinner("Auto scanning cropped label..."):
        results = decode_all(cropped_label)

    st.subheader("Scan Result")

    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)

        for i, row in enumerate(results, start=1):
            st.write(f"**{i}. Type:** {row['type']}")
            st.code(row["data"])
            st.caption(f"Variant: {row['variant']} | Angle: {row['angle']}°")
    else:
        st.warning("No QR / Data Matrix / barcode found from cropped label")
        st.info("Take closer image with label fully visible and less shadow")
