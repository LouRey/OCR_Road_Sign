import os
import shutil
import time
import yaml
from pathlib import Path

import streamlit as st
import cv2
import pytesseract
import easyocr
from ultralytics import YOLO
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

# === Configuration Tesseract ===
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
os.environ["TESSDATA_PREFIX"] = "/usr/share/tessdata"

# === Paths ===
PROJECT_PATH = Path(__file__).parent
TMP_DIR = PROJECT_PATH / "tmp"
MODEL_DIR = PROJECT_PATH / "models"
DEFAULT_MODEL = MODEL_DIR / "best.pt"
PARAMS_FILE = PROJECT_PATH / "conf" / "base" / "parameters_ocr.yml"
RAW_VIDEO = PROJECT_PATH / "data" / "01_raw" / "video.mp4"
UPLOADED_MODEL = PROJECT_PATH / "data" / "06_models" / "uploaded_model.pt"

# === Fonctions utilitaires ===
def clean_tmp(age_seconds: float = 3600):
    now = time.time()
    for path in TMP_DIR.glob("*"):
        try:
            if now - path.stat().st_mtime > age_seconds:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        except Exception:
            pass

def load_ocr_params() -> dict:
    with open(PARAMS_FILE, "r") as f:
        return yaml.safe_load(f) or {}

def save_ocr_params(params: dict):
    with open(PARAMS_FILE, "w") as f:
        yaml.dump(params, f)

# === Préparation ===
TMP_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
st.title("Pipeline OCR Kedro & Streamlit")
clean_tmp()

# === Upload de fichiers ===
st.sidebar.header("Uploader les fichiers requis")
video_uploaded = st.sidebar.file_uploader("Vidéo (.mp4)", type=["mp4"])
model_uploaded = st.sidebar.file_uploader("Modèle (.pt)", type=["pt"])

if video_uploaded:
    RAW_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_VIDEO, "wb") as f:
        f.write(video_uploaded.getbuffer())
    st.sidebar.success("Vidéo enregistrée.")

if model_uploaded:
    UPLOADED_MODEL.parent.mkdir(parents=True, exist_ok=True)
    with open(UPLOADED_MODEL, "wb") as f:
        f.write(model_uploaded.getbuffer())
    st.sidebar.success("Modèle enregistré.")

# === Exécution automatique si vidéo + modèle présents ===
if RAW_VIDEO.exists() and UPLOADED_MODEL.exists():
    st.success("Vidéo et modèle détectés. Exécution automatique du pipeline...")
    metadata = bootstrap_project(PROJECT_PATH)
    session = KedroSession.create(project_path=metadata.project_path)
    context = session.load_context()
    session.run()
    output_path = PROJECT_PATH / context.params["annotated_output_path"]
    if output_path.exists():
        st.success("Pipeline exécuté ! Voici la vidéo annotée :")
        st.video(str(output_path))
    else:
        st.error(f"Le pipeline s'est exécuté, mais introuvable : {output_path}")
    st.stop()

# === Mode manuel ===
mode = st.sidebar.selectbox("Mode d'exécution", [
    "Exécuter pipeline Kedro (modèle par défaut)",
    "Flux vidéo live"
])

if mode == "Exécuter pipeline Kedro (modèle par défaut)":
    st.header("Pipeline Kedro avec modèle par défaut")
    ocr_params = load_ocr_params()
    default_max = ocr_params.get("max_frames", 500)
    new_max = st.slider("Nombre maximum de frames à traiter", 1, 5000, default_max)
    if new_max != default_max:
        ocr_params["max_frames"] = new_max
        save_ocr_params(ocr_params)
        st.info(f"→ max_frames mis à jour dans {PARAMS_FILE.name} : {new_max}")

    model_files = list((PROJECT_PATH / "data" / "06_models").glob("*.pt"))
    can_run = RAW_VIDEO.exists() and model_files
    if not RAW_VIDEO.exists():
        st.warning("Aucune vidéo trouvée dans `data/01_raw/video.mp4`.")
    if not model_files:
        st.warning("Aucun modèle trouvé dans `data/06_models/*.pt`.")
    if can_run and st.button("Lancer le pipeline"):
        metadata = bootstrap_project(PROJECT_PATH)
        session = KedroSession.create(project_path=metadata.project_path)
        context = session.load_context()
        session.run()
        output_path = PROJECT_PATH / context.params["annotated_output_path"]
        if output_path.exists():
            st.success("Pipeline exécuté ! Voici la vidéo annotée :")
            st.video(str(output_path))
        else:
            st.error(f"Le pipeline s'est exécuté, mais introuvable : {output_path}")

elif mode == "Flux vidéo live":
    st.header("Flux vidéo live avec détection + OCR")
    use_easyocr = st.checkbox("Utiliser EasyOCR au lieu de Tesseract", value=False)
    reader = easyocr.Reader(['fr'], gpu=False) if use_easyocr else None

    cam_list = []
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cam_list.append(i)
            cap.release()
    if not cam_list:
        st.error("Aucune caméra détectée.")
    else:
        cam_index = st.selectbox("Caméra", cam_list)
        frame_interval = st.slider("Intervalle de détection (en nombre de frames)", min_value=1, max_value=30, value=10)

        if st.button("Démarrer le flux"):
            stframe_live = st.empty()
            stframe_annot = st.empty()
            cap = cv2.VideoCapture(cam_index)

            # Chargement modèle YOLO
            model_path = UPLOADED_MODEL if UPLOADED_MODEL.exists() else DEFAULT_MODEL
            model = YOLO(str(model_path))

            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                stframe_live.image(frame_rgb, channels="RGB", caption="Flux direct")

                if frame_count % frame_interval == 0:
                    result = model.predict(source=frame, conf=0.5, verbose=False)[0]
                    boxes = result.boxes.xyxy.cpu().numpy().astype(int)

                    for box in boxes:
                        x1, y1, x2, y2 = box[:4]
                        roi = frame[y1:y2, x1:x2]
                        if use_easyocr:
                            result_text = reader.readtext(roi)
                            text = result_text[0][-2] if result_text else ""
                        else:
                            text = pytesseract.image_to_string(roi, lang="fra")
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                    annotated_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    stframe_annot.image(annotated_rgb, channels="RGB", caption="Flux annoté")

                frame_count += 1

            cap.release()

# Nettoyage final
clean_tmp(age_seconds=0)
