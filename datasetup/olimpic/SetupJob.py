from pathlib import Path

from .. import DATASETS_DIR
from ..DatasetDownload import download_dataset

OLIMPIC_ENTRY_POINT = DATASETS_DIR / Path("olimpic-1.0-scanned/samples")
OLIMPIC_URL = "https://github.com/ufal/olimpic-icdar24/releases/download/datasets/olimpic-1.0-scanned.2024-02-12.tar.gz"


def download_olimpic():
    print("Downloading and setting up OLiMPiC dataset...")
    download_dataset(
        OLIMPIC_URL,
        DATASETS_DIR
    )
