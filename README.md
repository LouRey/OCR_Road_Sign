# 📦 OCR Panneaux Routiers - Jetson Nano & Mac (YOLOv8 + Tesseract + EasyOCR)

Ce guide vous permet d’installer, configurer et exécuter une application de détection et lecture de panneaux routiers sur Jetson Nano **et** sur Mac.

L’application repose sur Kedro, Streamlit, YOLOv8, Tesseract OCR et EasyOCR.

---

## 🔧 1. Installer un gestionnaire de conteneurs (Portainer, optionnel)

Portainer est une interface web pour gérer vos conteneurs Docker simplement (Jetson uniquement).

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

```
https://<IP_DE_LA_JETSON>:9443
```

---

## 🧬 2. Cloner le dépôt de l'application

```bash
git clone https://github.com/LouRey/OCR_Road_Sign.git
cd yolov8-ocr-app
```

---

## 🏗️ 3. Construire l'image Docker

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

> Cela retournera `/dev/video0`, `/dev/video1`, etc. si des caméras sont détectées.

Optionnel : pour plus d'infos sur les caméras :

```bash
sudo apt install v4l-utils
v4l2-ctl --list-devices
```

### 4.2 Lancer l'application

#### ➤ Sur Jetson (avec montage de la caméra)

```bash
docker run --rm -it \
  --net=host \
  --device=/dev/video0 \
  -v $(pwd):/app \
  -p 8501:8501 \
  yolov8-ocr-app:jetson
```

> 🔁 Pour monter plusieurs caméras, ajoute plusieurs `--device=/dev/videoX`

#### ➤ Sur Mac (sans accès caméra dans Docker)

📌 Recommandé : lancer **hors Docker** pour accéder à la webcam :

```bash
streamlit run app.py
```

Sinon :

```bash
docker run --rm -it \
  -v $(pwd):/app \
  -p 8501:8501 \
  yolov8-ocr-app:mac
```

Mais dans ce cas, la webcam intégrée ne fonctionnera pas dans le conteneur.

### 4.3 Accéder à l’interface Streamlit

```
http://localhost:8501  # ou http://<IP_JETSON>:8501
```

---

## 📤 5. Pousser l’image sur Docker Hub (optionnel)

```bash
docker tag yolov8-ocr-app:jetson tonuser/yolov8-ocr-app:jetson

docker login
# entrer vos identifiants Docker Hub

docker push tonuser/yolov8-ocr-app:jetson
```

---

## 🧪 6. Astuces de débogage

### Logs du conteneur

```bash
docker ps  # pour récupérer l’ID

docker logs <container_id>
```

### Vérifier la caméra (Jetson)

```bash
ls /dev/video*
sudo apt install v4l-utils
v4l2-ctl --list-devices
```
# 📷 Activer une caméra CSI sur Jetson Nano via SSH

Ce guide vous permet d’activer une caméra CSI (type IMX219) sur une Jetson Nano via une connexion SSH.

---

## ✅ Pré-requis

- Une caméra CSI (ex : **IMX219 – caméra officielle Raspberry Pi V2**) connectée au port CSI (nappe plate).
- Une connexion SSH fonctionnelle à la Jetson Nano.
- JetPack installé (au moins 4.4 ou supérieur recommandé).

---

## 🔧 Étapes de configuration

### 1. Lancer l’outil Jetson-IO
```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
```

> 💡 Cet outil s’utilise au clavier dans le terminal. Utilisez un terminal SSH compatible (ex : `gnome-terminal`, `iTerm`, `terminator`, etc.).

---

### 2. Naviguer dans les menus

#### a. Depuis le menu principal, sélectionner :
```
Configure Jetson Nano CSI Connector
```
(appuyez sur **Entrée**)

#### b. Ensuite, sélectionner :
```
Configure for compatible hardware
```
(appuyez sur **Entrée**)

---

### 3. Choisir le bon module caméra

Cochez le module adapté à votre caméra :

- Pour la caméra RPi V2 : cochez `Enable IMX219 Camera`

> Utilisez la **barre d’espace** pour cocher la case.

---

### 4. Enregistrer la configuration

- Naviguez jusqu’à `Save and Exit` avec les flèches
- Appuyez sur **Entrée**

---

### 5. Redémarrer la Jetson Nano
```bash
sudo reboot
```

---

## ✅ Vérification après redémarrage

### 1. Vérifier que la caméra est détectée :
```bash
ls /dev/video*
```

Résultat attendu :
```
/dev/video0
```

---

### 2. Tester le flux caméra (sans interface graphique) :
```bash
gst-launch-1.0 nvarguscamerasrc ! fakesink
```

> Si vous êtes connecté via HDMI, vous pouvez utiliser :
```bash
gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink
```

---

## 🛠️ En cas de problème

- Vérifiez que le ruban CSI est bien inséré dans le bon sens, bien enfoncé.
- Reprenez la configuration Jetson-IO pour vous assurer que l’option est bien cochée.
- Vérifiez les logs :
```bash
dmesg | grep -i imx
```

---

## 📌 Remarque

La caméra CSI ne peut être reconnue **qu’au démarrage** car elle dépend de la configuration du **device tree**.

---

---

## Pour lancer kubectl

kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml
kubectl port-forward service/yolov8-10-ocr-service 8501:8501

## 📚 Références

* Kedro : [https://kedro.readthedocs.io/](https://kedro.readthedocs.io/)
* Streamlit : [https://docs.streamlit.io/](https://docs.streamlit.io/)
* Tesseract : [https://tesseract-ocr.github.io/](https://tesseract-ocr.github.io/)
* EasyOCR : [https://github.com/JaidedAI/EasyOCR](https://github.com/JaidedAI/EasyOCR)
* YOLOv8 : [https://docs.ultralytics.com/models/yolov8/](https://docs.ultralytics.com/models/yolov8/)
* NVIDIA Jetson Containers : [https://catalog.ngc.nvidia.com/orgs/nvidia/containers](https://catalog.ngc.nvidia.com/orgs/nvidia/containers)
