import cv2
from kedro.io import AbstractDataset

class VideoDataSet(AbstractDataset):
    def __init__(self, filepath: str):
        self._filepath = filepath

    def _load(self):
        cap = cv2.VideoCapture(self._filepath)
        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {self._filepath}")
        return cap  # Tu pourras le lire frame par frame dans le nœud

    def _save(self, _):
        raise NotImplementedError("Saving video not supported.")

    def _describe(self):
        return dict(filepath=self._filepath)
