from pathlib import Path

from .. import DATASETS_DIR

# entry points for annotation and image retrieval
MUSCIMA_IMAGES_DIR = DATASETS_DIR / Path("cvcmuscima/CvcMuscima-Distortions")
MUSCIMA_ANNOTATIONS_DIR = DATASETS_DIR / Path("muscimapp/v1.0/data/cropobjects_withstaff")
MUSCIMA_SHARP_ENTRY_POINT = DATASETS_DIR / Path("muscima-sharp")

# datasets
MUSCIMAPP_URL = "https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11372/LRT-2372/MUSCIMA-pp_v1.0.zip"
CVCMUSCIMA_URL = "http://datasets.cvc.uab.es/muscima/CVCMUSCIMA_SR.zip"