# 📦 OCR Panneaux Routiers - Jetson Nano & Mac (YOLOv8 + Tesseract + EasyOCR)

Ce guide vous permet d’installer, configurer et exécuter une application de détection et lecture de panneaux routiers sur Jetson Nano **et** sur Mac.

L’application repose sur Kedro, Streamlit, YOLOv8, Tesseract OCR et EasyOCR.

---

## 🧬 1. Cloner le dépôt de l'application

```bash
git clone https://github.com/LouRey/OCR_Road_Sign.git
cd OCR_Road_Sign
```

---

## 🔧 2. Activer la caméra CSI sur Jetson Nano (si applicable)

### 2.1 Pré-requis

- Une caméra CSI (ex : IMX219 – caméra officielle Raspberry Pi V2)
- Une connexion SSH fonctionnelle à la Jetson Nano
- JetPack installé (version 4.4 minimum recommandée)

### 2.2 Configuration via SSH

```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
```

Naviguer dans les menus :
- `Configure Jetson Nano CSI Connector`
- `Configure for compatible hardware`
- Cochez `Enable IMX219 Camera` (ou votre modèle)
- Sauvegardez et quittez

### 2.3 Redémarrage

```bash
sudo reboot
```

### 2.4 Vérification

```bash
ls /dev/video*
gst-launch-1.0 nvarguscamerasrc ! fakesink
```

---

## 🐳 3. Construire l'image Docker

### 3.1 Sur Jetson Nano

```bash
docker build -f Dockerfile.jetson -t yolov8-ocr-app:jetson .
```

### 3.2 Sur Mac

```bash
docker build -f Dockerfile.mac -t yolov8-ocr-app:mac .
```

---

## 🚀 4. Exécuter l'application

### 4.1 Vérifier la présence d’une caméra (Jetson uniquement)

```bash
ls /dev/video*
```

Optionnel :

```bash
sudo apt install v4l-utils
v4l2-ctl --list-devices
```

### 4.2 Lancer l'application

#### ➤ Sur Jetson (avec caméra)

```bash
docker run --rm -it   --net=host   --device=/dev/video0   -v $(pwd):/app   -p 8501:8501   yolov8-ocr-app:jetson
```

#### ➤ Sur Mac (sans accès caméra en Docker)

Hors Docker (recommandé pour accès webcam) :

```bash
streamlit run app.py
```

Sinon (sans webcam) :

```bash
docker run --rm -it   -v $(pwd):/app   -p 8501:8501   yolov8-ocr-app:mac
```

### 4.3 Accéder à l’interface

```
http://localhost:8501  # ou http://<IP_JETSON>:8501
```

---

## 🧰 5. (Optionnel) Installer Portainer pour gérer les conteneurs (Jetson uniquement)

### 5.1 Vérifier Docker

```bash
docker version
docker info
```

Si erreur :
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 5.2 Installer Portainer

```bash
docker volume create portainer_data

docker run -d -p 8000:8000 -p 9443:9443   --name portainer   --restart=always   -v /var/run/docker.sock:/var/run/docker.sock   -v portainer_data:/data   portainer/portainer-ce:latest
```

### 5.3 Accéder à l’interface

```
https://<IP_DE_LA_JETSON>:9443
```

---

## ☁️ 6. Pousser l’image sur Docker Hub (optionnel)

```bash
docker tag yolov8-ocr-app:jetson tonuser/yolov8-ocr-app:jetson

docker login
docker push tonuser/yolov8-ocr-app:jetson
```

---

## 🧪 7. Astuces de débogage

### Logs

```bash
docker ps
docker logs <container_id>
```

### Caméra (Jetson)

```bash
ls /dev/video*
sudo apt install v4l-utils
v4l2-ctl --list-devices
```

---

## ☸️ 8. Lancer avec Kubernetes (optionnel)

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml
kubectl port-forward service/yolov8-10-ocr-service 8501:8501
```

---

## 📚 9. Références

- [Kedro](https://kedro.readthedocs.io/)
- [Streamlit](https://docs.streamlit.io/)
- [Tesseract](https://tesseract-ocr.github.io/)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [YOLOv8](https://docs.ultralytics.com/models/yolov8/)
- [NVIDIA Jetson Containers](https://catalog.ngc.nvidia.com/orgs/nvidia/containers)
