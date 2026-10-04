"""Constraining a language model's output to a typed schema.

From a contractor quoting platform, where a drawing or plan has to be turned into
measurements. The interesting part is not the model call, it is everything around
it: the response is constrained to a schema rather than parsed hopefully, every
extracted value carries a confidence, the instructions forbid guessing, and a
response that does not validate is an error rather than a silent empty result.
"""

import base64
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

VISION_MODEL_DEFAULT = "gpt-4.1-mini"


class DetectedMeasurement(BaseModel):
    label: str
    measurement_type: str
    shape: Literal["rectangle", "triangle", "trapezoid", "line", "count", "unknown"]
    width_ft: float | None = None
    height_ft: float | None = None
    base_ft: float | None = None
    top_width_ft: float | None = None
    bottom_width_ft: float | None = None
    length_ft: float | None = None
    quantity: float | None = None
    confidence: float = Field(ge=0, le=1)
    source_text: str | None = None


class OpeningMeasurement(BaseModel):
    opening_type: Literal["window", "door", "garage_door", "other"]
    quantity: float | None = None
    width_ft: float | None = None
    height_ft: float | None = None
    confidence: float = Field(ge=0, le=1)


class VisionExtractionResponse(BaseModel):
    trade: Literal["roofing", "siding", "unknown"]
    detected_measurements: list[DetectedMeasurement]
    openings: list[OpeningMeasurement]
    calculation_recommendations: list[str]
    warnings: list[str]
    confidence: float = Field(ge=0, le=1)


def image_to_base64_data_url(image_path: str) -> str:
    path = Path(image_path)
    suffix = path.suffix.lower().lstrip(".")
    mime_type_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
    mime_type = mime_type_map.get(suffix)
    if mime_type is None:
        raise ValueError(f"Unsupported image type: {path.suffix or suffix}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _build_instructions(trade_hint: str | None = None) -> str:
    """Say what the model must not do, not only what it must do."""
    trade_text = f"Trade hint: {trade_hint}." if trade_hint else "Trade hint: unknown."
    return (
        "Extract construction measurements visible in the uploaded image. "
        "Focus only on roofing and siding. Read typed or handwritten measurements if visible. "
        "Do not guess missing dimensions. If a dimension is unclear, return null and add a warning. "
        "If units are not visible, assume feet only if strongly implied; otherwise return null and add a warning. "
        "Do not calculate final quote price. Do not create material pricing. Do not estimate labor. "
        "Return structured JSON only. "
        f"{trade_text}"
    )


def _coerce_response(response) -> dict:
    """Prefer the parsed object, fall back to validating the raw text, refuse anything else."""
    parsed = getattr(response, "output_parsed", None)
    if parsed is not None:
        if hasattr(parsed, "model_dump"):
            return parsed.model_dump()
        if isinstance(parsed, dict):
            return parsed

    output_text = getattr(response, "output_text", None)
    if output_text:
        return VisionExtractionResponse.model_validate_json(str(output_text)).model_dump()

    raise RuntimeError("Vision response did not include parsed JSON output.")


def extract_measurements_from_image(image_path: str, trade_hint: str | None = None) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set before using image measurement extraction.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    data_url = image_to_base64_data_url(image_path)

    try:
        response = client.responses.parse(
            model=os.getenv("OPENAI_VISION_MODEL", VISION_MODEL_DEFAULT),
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": _build_instructions(trade_hint)},
                    {"type": "input_image", "image_url": data_url, "detail": "high"},
                ],
            }],
            text_format=VisionExtractionResponse,
        )
    except Exception as exc:
        raise RuntimeError(f"Vision extraction failed: {exc}") from exc

    try:
        return _coerce_response(response)
    except Exception as exc:
        raise RuntimeError(f"Vision extraction returned an unreadable response: {exc}") from exc
