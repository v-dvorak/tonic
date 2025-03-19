from pathlib import Path

from tqdm import tqdm

from odtools.Download import download_image
from . import DATASETS_DIR, MUSCIMAPP_URL, CVCMUSCIMA_URL
from ..DatasetDownload import download_dataset

# background storage
BACKGROUND_LIST = Path(__file__).parent / "backgrounds.txt"
BACKGROUNDS_DIR = DATASETS_DIR / Path("backgrounds")
BACKGROUNDS_DIR.mkdir(exist_ok=True, parents=True)


def download_background_images():
    with open(BACKGROUND_LIST, "r") as f:
        background_list = f.read().splitlines()

    for background_id in tqdm(background_list):
        download_image(background_id, Path(background_id + ".png"), BACKGROUNDS_DIR)


def download_muscima():
    download_dataset(MUSCIMAPP_URL, DATASETS_DIR / "muscimapp")
    download_dataset(CVCMUSCIMA_URL, DATASETS_DIR / "cvcmuscima")
