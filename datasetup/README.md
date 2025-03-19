# DataSetup

This directory contains all scripts necessary to download and build these datasets:

- [MUSCIMA#](MuscimaSharp/README.md)
- [MuNG to OLA](mung2ola/README.md)
- [OLiMPiC test dataset](olimpic/README.md)

# Download and build all datasets

MuNG to OLA cannot be run as a simple job - the dataset is not publicly available, see the [documentation](mung2ola/README.md).

After cloning TonIC, set up a virtual environment and install requirements via pip:

```
pip install -r requirements.txt
```

And run the download script from the `tonic` directory:

```
python3 -m datasetup
```

All the data necessary will be automatically downloaded and datasets will be built.
