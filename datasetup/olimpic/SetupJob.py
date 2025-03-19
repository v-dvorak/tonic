from . import DATASETS_DIR, OLIMPIC_URL
from ..DatasetDownload import download_dataset


def download_olimpic():
    print("Downloading and setting up OLiMPiC dataset...")
    download_dataset(
        OLIMPIC_URL,
        DATASETS_DIR
    )
