from .MuscimaSharp.SetupJob import run_muscima_sharp_setup
from .olimpic.SetupJob import download_olimpic

if __name__ == "__main__":
    download_olimpic()
    run_muscima_sharp_setup()
