import tarfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from tqdm import tqdm


def download_and_extract(url: str, destination_folder: Path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # extract filename from URL using pathlib
        parsed_url = urlparse(url)
        file_name = Path(parsed_url.path).name

        if not file_name:
            print("Error: URL does not contain a file name.")
            return False

        # define the local path for the downloaded file
        destination_folder = Path(destination_folder)
        file_path = destination_folder / file_name

        # get the total size of the file from the response headers
        total_size = int(response.headers.get('content-length', 0))

        with open(file_path, 'wb') as zip_file, tqdm(
                desc="Downloading",
                total=total_size,
                unit="B",
                unit_scale=True,
                ncols=100
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    zip_file.write(chunk)
                    bar.update(len(chunk))

        print(f"\nDownloaded the zip file to {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download the file: {e}")
        return False

    # unzip the file
    try:
        if file_name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(destination_folder)
            print(f"Extracted ZIP contents to {destination_folder}")

        elif file_name.endswith('.tar.gz'):
            with tarfile.open(file_path, 'r:gz') as tar_ref:
                tar_ref.extractall(destination_folder)
            print(f"Extracted TAR.GZ contents to {destination_folder}")

        else:
            print("Unsupported file format.")
            return False

    except (zipfile.BadZipFile, tarfile.TarError) as e:
        print(f"Extraction error: {e}")
        return False

    # delete the original ZIP file if extraction was successful
    try:
        file_path.unlink()  # pathlib method to delete the file
        print(f"Successfully deleted the original zip file: {file_path}")
    except OSError as e:
        print(f"Error deleting the file: {e}")
        return False

    return True


def download_dataset(url: str, destination_folder: Path):
    destination_folder.mkdir(exist_ok=True, parents=True)

    if download_and_extract(url, destination_folder):
        print("Download, extraction, and cleanup were successful.")
    else:
        print("There was an error in the process.")
    print()
