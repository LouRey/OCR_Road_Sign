import torch
from kedro.io import AbstractDataset


class TorchModelDataSet(AbstractDataset):
    def __init__(self, filepath: str, map_location: str = "cpu"):
        self._filepath = filepath
        self._map_location = map_location

    def _load(self):
        return torch.load(self._filepath, map_location=self._map_location, weights_only=False)

    def _save(self, model):
        torch.save(model, self._filepath)

    def _describe(self):
        return dict(filepath=self._filepath, map_location=self._map_location)
