from pathlib import Path

import cv2
import math
from PIL import Image

from odtools import BoundingBox
from odtools.Inference import InferenceJob, SplitSettings, run_multiple_prediction_jobs, IModelWrapper
from tonic import NOTEHEAD_TYPE_TAG, NoteheadType, NodeName, Node, reconstruct_note_events, LMXWrapper, \
    linearize_note_events_to_lmx
from tonic import (preprocess_annots_for_reconstruction)
from tonic import (refactor_measures_on_page)
from tonic.Reconstruction.VizUtils import visualize_input_data


def run_predictions_single_image(
        image_path: Path,
        staff_detector: IModelWrapper,
        notehead_detector: IModelWrapper,
        verbose: bool = False,
        visualize: bool = False,
) -> tuple[list[Node], list[Node], list[Node]]:
    """
    returns: measures, grand staffs, noteheads
    """
    # SETUP INFERENCE JOBS
    # convert image to bw beforehand
    # (color to bw conversion from cv2 does not work in this case)
    loaded_image = Image.open(image_path)
    bw_image = loaded_image.convert("L")

    image_width, image_height = loaded_image.size

    # staff
    staff_job = InferenceJob(
        image=bw_image,
        model_wrapper=staff_detector,
        # retrieve only measures and grand staffs
        wanted_ids=[1, 4]
    )

    # noteheads
    notehead_job = InferenceJob(
        image=cv2.imread(image_path),
        model_wrapper=notehead_detector,
        # retrieve only full and empty noteheads
        wanted_ids=[0, 1],
        split_settings=SplitSettings(
            width=image_height,
            height=image_height,
            overlap_ratio=0.10,
            iou_threshold=0.25,
            edge_offset_ratio=0.04
        )
    )

    # RUN INFERENCE JOBS
    combined = run_multiple_prediction_jobs(
        [
            staff_job,
            notehead_job,
        ],
        verbose=False
    )

    if verbose:
        print(f"Class names: {', '.join(combined.class_names)}")
        print()

    # INITIALIZE GRAPH
    prepro_def = [
        (
            NodeName.MEASURE, combined.annotations[0]
        ),
        (
            NodeName.GRAND_STAFF, combined.annotations[1]
        ),
        (
            NodeName.NOTEHEAD, [NOTEHEAD_TYPE_TAG],
            [
                (combined.annotations[2], [NoteheadType.FULL]),
                (combined.annotations[3], [NoteheadType.HALF])
            ]
        ),
    ]

    measures, grand_staffs, noteheads = preprocess_annots_for_reconstruction(prepro_def)

    if visualize:
        visualize_input_data(
            image_path,
            measures,
            notehead_full=noteheads,
            notehead_half=grand_staffs
        )

    return measures, grand_staffs, noteheads


def refine_detections(
        image_path: Path,
        measures: list[Node],
        grand_staffs: list[Node],
        noteheads: list[Node],
        vertical_offset_factor: float,
        verbose: bool = False,
        visualize: bool = False,
) -> tuple[list[Node], list[Node], list[Node]]:
    """
    returns: measures, grand_staffs, noteheads
    """
    image_width, image_height = Image.open(image_path).size

    refactor_measures_on_page(
        measures,
        image_path,
        verbose=verbose,
        visualize=False
    )

    valid_box = BoundingBox(
        0,
        math.ceil(image_height * vertical_offset_factor),
        image_width,
        math.ceil(image_height * (1 - vertical_offset_factor))
    )

    measures: list[Node]
    measures = [m for m in measures if m.annot.bbox.is_fully_inside(valid_box)]
    grand_staffs = [gs for gs in grand_staffs if gs.annot.bbox.is_fully_inside(valid_box)]

    if visualize:
        visualize_input_data(
            image_path,
            measures,
            notehead_full=noteheads,
            notehead_half=grand_staffs
        )

    return measures, grand_staffs, noteheads


def detections_to_lmx_wrapper(
        measures: list[Node],
        grand_staffs: list[Node],
        noteheads: list[Node],
        verbose: bool = False,
) -> LMXWrapper:
    events = reconstruct_note_events(
        measures,
        grand_staffs,
        noteheads,
        ual_factor=1.8,
        neiou_threshold=0.4,
        verbose=verbose
    )

    return linearize_note_events_to_lmx(events)


def process_single_olimpic_image(
        image_path: Path,
        staff_detector: IModelWrapper,
        notehead_detector: IModelWrapper,
        vertical_offset_factor: float = None,
        verbose: bool = False,
        visualize: bool = False
) -> LMXWrapper:
    """
    Predicts noteheads, staff and grand staff for a single image from the OLiMPiC dataset.

    :param image_path: Path to an image
    :param staff_detector: wrapped model for staff and grand staff detection
    :param notehead_detector: wrapped model for notehead detection
    :param vertical_offset_factor: how much to offset safe zone from image edges relative to image height,
    defaults to 0.2
    :param verbose: make script verbose
    :param visualize: visualize inference
    """
    if vertical_offset_factor is None:
        vertical_offset_factor = 0.2

    measures, grand_staffs, noteheads = run_predictions_single_image(
        image_path,
        staff_detector,
        notehead_detector,
        verbose=verbose,
        visualize=visualize
    )
    measures, grand_staffs, noteheads = refine_detections(
        image_path,
        measures, grand_staffs, noteheads,
        vertical_offset_factor=vertical_offset_factor,
        verbose=verbose,
        visualize=visualize
    )
    return detections_to_lmx_wrapper(measures, grand_staffs, noteheads)
