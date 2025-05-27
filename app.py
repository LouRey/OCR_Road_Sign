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

# Upload vidéo & modèle dans la sidebar
st.sidebar.header("Uploader les fichiers requis")
video_uploaded = st.sidebar.file_uploader("Vidéo (.mp4)", type=["mp4"], key="video")
model_uploaded = st.sidebar.file_uploader("Modèle (.pt)", type=["pt"], key="model")

uploaded_video_path = PROJECT_PATH / "data" / "01_raw" / "video.mp4"
uploaded_model_path = PROJECT_PATH / "data" / "06_models" / "uploaded_model.pt"

if video_uploaded:
    uploaded_video_path.parent.mkdir(parents=True, exist_ok=True)
    with open(uploaded_video_path, "wb") as f:
        f.write(video_uploaded.getbuffer())
    st.sidebar.success("Vidéo enregistrée.")

if model_uploaded:
    uploaded_model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(uploaded_model_path, "wb") as f:
        f.write(model_uploaded.getbuffer())
    st.sidebar.success("Modèle enregistré.")

# Exécution auto si les deux fichiers sont présents
if uploaded_video_path.exists() and uploaded_model_path.exists():
    st.success("Vidéo et modèle détectés. Exécution automatique du pipeline...")

    metadata = bootstrap_project(PROJECT_PATH)
    session = KedroSession.create(project_path=metadata.project_path)
    context = session.load_context()
    session.run()

    rel_out = context.params["annotated_output_path"]
    output_path = PROJECT_PATH / rel_out

    if output_path.exists():
        st.success("Pipeline exécuté ! Voici la vidéo annotée :")
        st.video(str(output_path))
    else:
        st.error(f"Le pipeline s'est exécuté, mais introuvable : {output_path}")
    st.stop()

# Choix du mode
mode = st.sidebar.selectbox(
    "Mode d'exécution",
    [
        "Exécuter pipeline Kedro (modèle par défaut)",
        "Flux vidéo live",
    ],
)

# === Mode 1 : pipeline Kedro avec modèle par défaut ===
if mode == "Exécuter pipeline Kedro (modèle par défaut)":
    st.header("Pipeline Kedro avec modèle par défaut")

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

    video_path = PROJECT_PATH / "data" / "01_raw" / "video.mp4"
    model_dir = PROJECT_PATH / "data" / "06_models"
    model_files = list(model_dir.glob("*.pt"))

    if not video_path.exists():
        st.warning("Aucune vidéo trouvée dans `data/01_raw/video.mp4`.")
    if not model_files:
        st.warning("Aucun modèle trouvé dans `data/06_models/*.pt`.")

    can_run = video_path.exists() and model_files

    if can_run and st.button("Lancer le pipeline", disabled=not can_run):
        metadata = bootstrap_project(PROJECT_PATH)
        session = KedroSession.create(project_path=metadata.project_path)
        context = session.load_context()
        session.run()

        rel_out = context.params["annotated_output_path"]
        output_path = PROJECT_PATH / rel_out

        if output_path.exists():
            st.success("Pipeline exécuté ! Voici la vidéo annotée :")
            st.video(str(output_path))
        else:
            st.error(f"Le pipeline s'est exécuté, mais introuvable : {output_path}")

# === Mode 2 : flux vidéo live ===
elif mode == "Flux vidéo live":
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
