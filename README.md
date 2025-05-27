# 📦 OCR Panneaux Routiers - Jetson Nano (YOLOv8 + Tesseract)

Ce guide vous permet d’installer, configurer et exécuter une application de détection et lecture de panneaux routiers sur une Jetson Nano via Docker.

L’application repose sur Kedro, Streamlit, YOLOv8 et Tesseract OCR.

---

## 🔧 1. Installer un gestionnaire de conteneurs (Portainer)

Portainer est une interface web pour gérer vos conteneurs Docker simplement.

### 1.1 Vérifier que Docker fonctionne

```bash
docker version
docker info
```

Si vous avez une erreur du type `Got permission denied while trying to connect to the Docker daemon socket` :

```bash
sudo usermod -aG docker $USER
newgrp docker
```

> ✅ Redémarrez votre terminal ou votre Jetson si besoin.

### 1.2 Tester si Portainer est déjà installé

```bash
docker ps | grep portainer
```

Si rien n'est retourné, Portainer n'est pas encore installé.

### 1.3 Installer Portainer si besoin

```bash
docker volume create portainer_data

docker run -d -p 8000:8000 -p 9443:9443 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

### 1.4 Accéder à l’interface

Dans un navigateur connecté au réseau local :

```
https://<IP_DE_LA_JETSON>:9443
```

Créez un compte admin, connectez le "Local Docker environment".

---

## 🧬 2. Cloner le dépôt de l'application

```bash
git clone https://github.com/tonuser/yolov8-ocr-app.git
cd yolov8-ocr-app
```

---

## 🏗️ 3. Construire l'image Docker sur la Jetson

Assurez-vous d'être bien sur la Jetson avec une version de JetPack 5.x.

### 3.1 Build de l'image avec le Dockerfile Jetson

```bash
docker build -f Dockerfile.jetson -t yolov8-ocr-app:jetson .
```

> ⚠️ Cette commande peut prendre plusieurs minutes.

---

## 🚀 4. Exécuter l'application

### 4.1 Vérifier la présence de la caméra

Sur Jetson uniquement (non applicable sur Mac) :

```bash
ls /dev/video*
```

Si cette commande ne retourne rien, cela signifie qu'aucun périphérique vidéo compatible (comme une webcam USB) n’est détecté. Dans ce cas, exécutez sans monter la caméra.

### 4.2 Lancer le conteneur via docker-compose

**Sur Jetson, vous pouvez lancer avec la variable VIDEO\_DEVICE définie :**

```bash
VIDEO_DEVICE=/dev/video0 docker compose up --build
```

**Sur Mac ou si aucune caméra n'est présente, lancez simplement :**

```bash
docker compose up --build
```

L’application détectera dynamiquement la caméra dans l’interface Streamlit (si supporté).

### 4.3 Accès à l’interface Streamlit

```
http://<IP_DE_LA_JETSON>:8501
```

---

## 📄 5. Pousser l’image sur Docker Hub (optionnel)

```bash
docker tag yolov8-ocr-app:jetson tonuser/yolov8-ocr-app:jetson

docker login
# entrer votre identifiant et mot de passe Docker Hub

docker push tonuser/yolov8-ocr-app:jetson
```

---

## ✅ 6. Astuces de débogage

### Accès aux logs d'un conteneur en cours

```bash
docker ps  # pour récupérer l’ID du conteneur
docker logs <container_id>
```

### Lister les caméras disponibles (Jetson uniquement)

```bash
ls /dev/video*
```

### Tester le flux vidéo manuellement (Jetson uniquement)

```bash
sudo apt install v4l-utils
v4l2-ctl --list-devices
```

---

## 📚 Références

* Kedro: [https://kedro.readthedocs.io/](https://kedro.readthedocs.io/)
* Streamlit: [https://docs.streamlit.io/](https://docs.streamlit.io/)
* Tesseract: [https://tesseract-ocr.github.io/](https://tesseract-ocr.github.io/)
* YOLOv8: [https://docs.ultralytics.com/models/yolov8/](https://docs.ultralytics.com/models/yolov8/)
* NVIDIA Jetson Containers: [https://catalog.ngc.nvidia.com/orgs/nvidia/containers](https://catalog.ngc.nvidia.com/orgs/nvidia/containers)
