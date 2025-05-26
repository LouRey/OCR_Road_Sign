import os
import shutil
import time
import yaml
from pathlib import Path

import streamlit as st
import cv2
import pytesseract
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from src.kedro_road_sign.pipelines.ocr.nodes import detect_and_ocr, annotate_video

# === Configuration Tesseract dans le container ===
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
os.environ["TESSDATA_PREFIX"] = "/usr/share/tessdata"
# ===============================================

# Chemins du projet
PROJECT_PATH = Path(__file__).parent
TMP_DIR = PROJECT_PATH / "tmp"
MODEL_DIR = PROJECT_PATH / "models"
DEFAULT_MODEL = MODEL_DIR / "best.pt"
PARAMS_FILE = PROJECT_PATH / "conf" / "base" / "parameters_ocr.yml"

# Fonction de nettoyage du dossier tmp
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

# Chargement / sauvegarde des paramètres OCR
def load_ocr_params() -> dict:
    with open(PARAMS_FILE, "r") as f:
        return yaml.safe_load(f) or {}

def save_ocr_params(params: dict):
    with open(PARAMS_FILE, "w") as f:
        yaml.dump(params, f)

# Préparations des dossiers
TMP_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# Titre de l'app
st.title("Pipeline OCR Kedro & Streamlit")

# Nettoyage d'anciennes données
clean_tmp()

# Choix du mode
mode = st.sidebar.selectbox(
    "Mode d'exécution",
    [
        "Exécuter pipeline Kedro (modèle par défaut)",
        "Uploader un nouveau modèle & exécuter",
        "Flux vidéo live",
    ],
)

# === Mode 1 : pipeline Kedro avec modèle par défaut ===
if mode == "Exécuter pipeline Kedro (modèle par défaut)":
    st.header("Pipeline Kedro avec modèle par défaut")

    # Slider pour max_frames (modifie directement le YAML)
    ocr_params = load_ocr_params()
    default_max = ocr_params.get("max_frames", 500)
    new_max = st.slider(
        "Nombre maximum de frames à traiter",
        min_value=1,
        max_value=5000,
        value=default_max,
        step=1,
    )
    if new_max != default_max:
        ocr_params["max_frames"] = int(new_max)
        save_ocr_params(ocr_params)
        st.info(f"→ max_frames mis à jour dans {PARAMS_FILE.name} : {new_max}")

    if st.button("Lancer le pipeline"):
        # Bootstrap et session Kedro
        metadata = bootstrap_project(PROJECT_PATH)
        session = KedroSession.create(project_path=metadata.project_path)
        context = session.load_context()
        session.run()  # exécute le pipeline __default__ (OCR)

        # Récupérer le chemin de sortie depuis les params Kedro
        rel_out = context.params["annotated_output_path"]
        output_path = PROJECT_PATH / rel_out

        if output_path.exists():
            st.success("Pipeline exécuté ! Voici la vidéo annotée :")
            st.video(str(output_path))
        else:
            st.error(f"Le pipeline s'est exécuté, mais introuvable : {output_path}")

# === Mode 2 : upload & exécution avec nouveau modèle ===
elif mode == "Uploader un nouveau modèle & exécuter":
    st.header("Upload & exécution avec nouveau modèle")
    uploaded_file = st.file_uploader("Choisir un fichier .pt", type=["pt"])
    if uploaded_file is not None:
        model_path = TMP_DIR / uploaded_file.name
        with open(model_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.write(f"Modèle sauvegardé: {model_path}")

        if st.button("Lancer le pipeline avec ce modèle"):
            # On suppose que le fichier vidéo d'entrée est déjà présent dans tmp/input.mp4
            input_video = TMP_DIR / "input.mp4"
            rois = detect_and_ocr(
                video_path=str(input_video),
                model_path=str(model_path),
                max_frames=ocr_params.get("max_frames", 500),
            )
            output_path = TMP_DIR / "annotated_output.mp4"
            annotate_video(
                video_path=str(input_video),
                rois_with_texts=rois,
                model_path=str(model_path),
                output_path=str(output_path),
            )
            st.video(str(output_path))
            texts = [text for _, text in rois]
            st.write("Textes détectés :", texts)

# === Mode 3 : flux vidéo live ===
else:
    st.header("Flux vidéo live")
    st.write("Sélectionnez la caméra disponible :")
    cams = []
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cams.append(i)
            cap.release()
    cam_index = st.selectbox("Caméra", cams)
    if st.button("Démarrer le flux"):
        cap = cv2.VideoCapture(cam_index)
        stframe = st.empty()
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            stframe.image(frame, channels="RGB")
        cap.release()

# Nettoyage final (optionnel)
clean_tmp(age_seconds=0)
