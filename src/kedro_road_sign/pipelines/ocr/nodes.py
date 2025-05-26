"""
Boilerplate pipeline 'ocr' avec optimisations pour:
- Debug avec frame limit
- Un seul passage sur les frames
- Filtrage des classes
- Annotation directe
"""

import os
import cv2
import torch
import pytesseract
import numpy as np
from ultralytics import YOLO
from shapely.geometry import box
import unicodedata
import re
import logging

logger = logging.getLogger(__name__)
#os.environ["TESSDATA_PREFIX"] = "/opt/homebrew/share/tessdata/"

def _get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")

def _clean_ocr_text(text: str) -> str:
    if not text:
        return "###"
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[\n\r\t]", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s\-.,]", "", text)
    return text.strip() if text.strip() else "###"

def _iou(box1, box2):
    b1 = box(*box1)
    b2 = box(*box2)
    inter = b1.intersection(b2).area
    union = b1.union(b2).area
    return inter / union if union else 0

def detect_and_ocr(video_path: str, model_path: str, max_frames: int = 0) -> list:
    cap = cv2.VideoCapture(video_path)
    model = YOLO(model_path)
    rois_with_texts = []
    seen_boxes = []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"[DETECTION+OCR] Total frames: {total_frames}, Max to process: {max_frames if max_frames else 'ALL'}")

    frame_index = 0
    text_counter = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1
        if max_frames and frame_index > max_frames:
            break

        if frame_index % 10 == 0 or frame_index == 1:
            logger.info(f"[FRAME] Processing {frame_index}/{total_frames}")

        results = model.predict(source=frame, verbose=False)
        for result in results:
            for box_tensor, cls_tensor in zip(result.boxes.xyxy.cpu().numpy(), result.boxes.cls.cpu().numpy()):
                x1, y1, x2, y2 = map(int, box_tensor[:4])
                label = result.names[int(cls_tensor)].lower()
                if label == "other-sign":
                    continue

                this_box = (x1, y1, x2, y2)
                if any(_iou(this_box, seen) > 0.7 for seen in seen_boxes):
                    continue

                seen_boxes.append(this_box)
                roi = frame[y1:y2, x1:x2]
                if roi.size > 0:
                    roi = cv2.resize(roi, (200, 200))
                    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                    raw_text = pytesseract.image_to_string(thresh, lang='fra').strip()
                    text = _clean_ocr_text(raw_text)
                    logger.info(f"[OCR] ROI {text_counter + 1}: '{text}'")
                    rois_with_texts.append((this_box, text))
                    text_counter += 1

    cap.release()
    logger.info(f"[OCR] Finished. Unique panels: {len(rois_with_texts)}")
    return rois_with_texts

def annotate_video(video_path: str, rois_with_texts: list, model_path: str, output_path: str = "data/08_reporting/annotated.mp4", max_frames: int = 0) -> str:
    
    # —> Suppression du fichier de sortie existant
    if os.path.exists(output_path):
        os.remove(output_path)
        logger.info(f"[ANNOTATION] Ancien fichier supprimé : {output_path}")
    
    cap = cv2.VideoCapture(video_path)
    model = YOLO(model_path)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_index = 0
    text_pointer = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1
        if max_frames and frame_index > max_frames:
            break

        results = model.predict(source=frame, verbose=False)
        for result in results:
            for box_tensor, cls_tensor in zip(result.boxes.xyxy.cpu().numpy(), result.boxes.cls.cpu().numpy()):
                x1, y1, x2, y2 = map(int, box_tensor[:4])
                label = result.names[int(cls_tensor)].lower()

                if label == "other-sign":
                    continue

                if text_pointer < len(rois_with_texts):
                    _, text = rois_with_texts[text_pointer]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame, text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                    )
                    text_pointer += 1

        out.write(frame)

    cap.release()
    out.release()
    logger.info(f"[ANNOTATION] Video saved to {output_path}")
    #return output_path
