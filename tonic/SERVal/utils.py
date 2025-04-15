from ..Linearization import LMXWrapper


def compute_LMX_metrics(predicted_lmx: LMXWrapper, ground_truth_lmx: LMXWrapper) -> tuple[float, float, float, float]:
    """
    Computes Symbol Error Rate for two LMXWrappers.
    Returns the SER of standardized, reduced, melody and contour format.

    :param predicted_lmx: LMXWrapper prediction
    :param ground_truth_lmx: LMXWrapper ground truth
    :return: SER of standardized, reduced, melody and contour format
    """
    standardized = LMXWrapper.normalized_levenstein_distance(
        predicted_lmx.tokens,
        ground_truth_lmx.tokens
    )
    reduced = LMXWrapper.normalized_levenstein_distance(
        predicted_lmx.to_reduced(),
        ground_truth_lmx.to_reduced()
    )
    melody = LMXWrapper.normalized_levenstein_distance(
        predicted_lmx.to_melody(),
        ground_truth_lmx.to_melody()
    )
    contour = LMXWrapper.normalized_levenstein_distance(
        predicted_lmx.to_contour(),
        ground_truth_lmx.to_contour()
    )

    return standardized, reduced, melody, contour
