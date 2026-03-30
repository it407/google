import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import cv2
from pyzbar.pyzbar import decode

st.set_page_config(page_title="QR & Label Code Scanner", layout="wide")

st.title("QR Code and Label Code Scanner")
st.write("Upload an image or capture from camera to scan QR codes and barcodes.")

def scan_codes(pil_image):
    """
    Scan QR / barcode from image using pyzbar.
    Returns:
        decoded_results: list of decoded objects
        output_image: image with boxes drawn
    """
    img = np.array(pil_image.convert("RGB"))
    decoded_results = decode(img)

    draw = ImageDraw.Draw(pil_image)

    results = []
    for obj in decoded_results:
        x, y, w, h = obj.rect.left, obj.rect.top, obj.rect.width, obj.rect.height

        # Draw bounding box
        draw.rectangle([(x, y), (x + w, y + h)], outline="green", width=4)

        code_data = obj.data.decode("utf-8", errors="ignore")
        code_type = obj.type

        # Draw label text
        label = f"{code_type}: {code_data}"
        draw.text((x, max(y - 20, 0)), label, fill="green")

        results.append({
            "type": code_type,
            "data": code_data
        })

    return results, pil_image


def try_qr_opencv(pil_image):
    """
    Fallback QR scan using OpenCV QRCodeDetector.
    Useful if pyzbar misses QR.
    """
    img = np.array(pil_image.convert("RGB"))
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img)

    results = []
    if points is not None and data:
        pts = points[0].astype(int)
        draw = ImageDraw.Draw(pil_image)

        for i in range(len(pts)):
            p1 = tuple(pts[i])
            p2 = tuple(pts[(i + 1) % len(pts)])
            draw.line([p1, p2], fill="blue", width=4)

        draw.text((pts[0][0], max(pts[0][1] - 20, 0)), f"QR: {data}", fill="blue")
        results.append({
            "type": "QRCODE",
            "data": data
        })

    return results, pil_image


input_mode = st.radio("Select input source", ["Upload Image", "Camera Capture"])

image = None

if input_mode == "Upload Image":
    uploaded_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)

else:
    camera_file = st.camera_input("Capture image")
    if camera_file:
        image = Image.open(camera_file)

if image:
    st.subheader("Original Image")
    st.image(image, use_container_width=True)

    if st.button("Scan Now"):
        working_image = image.copy()

        # First try pyzbar for barcode + QR
        results, marked_image = scan_codes(working_image)

        # If nothing found, try OpenCV QR fallback
        if not results:
            working_image = image.copy()
            qr_results, marked_image = try_qr_opencv(working_image)
            results.extend(qr_results)

        st.subheader("Scanned Output")
        st.image(marked_image, use_container_width=True)

        if results:
            st.success(f"Found {len(results)} code(s)")
            for i, item in enumerate(results, start=1):
                st.write(f"**{i}. Type:** {item['type']}")
                st.write(f"**Data:** `{item['data']}`")
                st.write("---")
        else:
            st.warning("No QR code or barcode detected.")
