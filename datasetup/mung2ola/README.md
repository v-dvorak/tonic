# MuNG to OLA 

MuNG format definition does not support annotations of "large" objects, such as measures and system measures, as it is designed for describing musical symbols rather than structural elements of the score.

We use simple rules to create desired OLA objects - system measures, measures, staffs, system, grand staffs - from the original MuNG format.

## Build the dataset

After cloning TonIC, set up a virtual environment and install requirements via pip:

```
pip install -r requirements.txt
```

And run the build script from the `tonic` directory:

```
python3 -m datasetup.mung2ola "output_dir" "image_dir" "annot_dir"
```

For implementation details see [Algorithm Description](docs/algorithm-description.md).

## Image Examples

<p float="middle">
  <img src="docs/mung-good-example.PNG" width="45%" />
  <img src="docs/mung-bad-example.PNG" width="45%" />
</p>

## Limitations and known issues

**Note:** This might change with later versions, issues described are caused by scripts for exporting annotations to MuNG or even by mistakes in annotations themselves.
- Staff groupings might be duplicated
- Staff groupings and barlines can overlap
- Double barlines are just two barlines close together
- Bounding boxes of measure separators and staffs are imprecise

## References

### MuNG

> Jan Hajič jr., Pavel Pecina. In Search of a Dataset for Handwritten Optical Music Recognition: Introducing MUSCIMA++. CoRR, arXiv:1703.04824, 2017. https://arxiv.org/abs/1703.04824.
