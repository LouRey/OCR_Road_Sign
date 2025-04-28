from kedro.pipeline import Pipeline, node, pipeline
from .nodes import detect_and_ocr, annotate_video

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=detect_and_ocr,
            inputs=[
                "params:original_video_path",
                "params:model_path",
                "params:max_frames"
            ],
            outputs="rois_with_texts",
            name="detect_and_ocr_node"
        ),
        node(
            func=annotate_video,
            inputs=[
                "params:original_video_path",
                "rois_with_texts",
                "params:model_path",
                "params:annotated_output_path",
                "params:max_frames"
            ],
            outputs=None,
            name="annotate_video_node"
        )
    ])
