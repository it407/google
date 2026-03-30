import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import cv2

st.set_page_config(page_title="QR Code Scanner", layout="wide")
st.title("QR Code Scanner via Streamlit")

def scan_qr_opencv(pil_image):
    img = np.array(pil_image.convert("RGB"))
    detector = cv2.QRCodeDetector()

    data, points, _ = detector.detectAndDecode(img)

    output = pil_image.copy()
    draw = ImageDraw.Draw(output)

    results = []

    if points is not None and data:
        pts = points[0].astype(int)

        for i in range(len(pts)):
            p1 = tuple(pts[i])
            p2 = tuple(pts[(i + 1) % len(pts)])
            draw.line([p1, p2], fill="green", width=4)

        x, y = pts[0]
        draw.text((int(x), max(int(y) - 25, 0)), f"QR: {data}", fill="green")

        results.append({
            "type": "QRCODE",
            "data": data
        })

    return results, output

mode = st.radio("Select input source", ["Upload Image", "Camera"])
image = None

if mode == "Upload Image":
    uploaded_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
else:
    camera_file = st.camera_input("Take photo")
    if camera_file:
        image = Image.open(camera_file)

if image:
    st.subheader("Original Image")
    st.image(image, use_container_width=True)

    if st.button("Scan QR"):
        results, marked = scan_qr_opencv(image)

        st.subheader("Scanned Output")
        st.image(marked, use_container_width=True)

        if results:
            st.success("QR code detected")
            for r in results:
                st.write(f"**Type:** {r['type']}")
                st.code(r["data"])
        else:
            st.warning("No QR code found")
