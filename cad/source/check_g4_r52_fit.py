"""Review G4 STEP envelopes against the R5.2 core and ADF50 V0.4 envelopes."""

import json
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
G4 = ROOT / "ZL80_R52_G4_20261116/cad/assemblies"
MIN_VOLUME = 0.01


def read_step(path):
    for shape, name, location, _ in cq.Assembly.load(str(path)):
        parts = name.split("/")
        name = parts[-2] if parts[-1].isdigit() else parts[-1]
        yield name, shape.moved(location)


def intersections(objects, context):
    findings = []
    for name, shape in objects:
        first = shape.BoundingBox()
        for other, target, second in context:
            if any(
                min(getattr(first, axis + "max"), getattr(second, axis + "max"))
                <= max(getattr(first, axis + "min"), getattr(second, axis + "min"))
                for axis in "xyz"
            ):
                continue
            volume = shape.intersect(target).Volume()
            if volume > MIN_VOLUME:
                expected = name == "B01_JPMT1" and "_P04_PMT_pin_" in other
                findings.append({
                    "object": name, "context": other, "mm3": round(volume, 3),
                    "status": "SOCKET_PIN_OCCUPANCY" if expected else "REVIEW",
                })
    return findings


def main():
    board_proxies = {"B01", "B06", "B07", "B08"}
    detector_proxies = {"PD_sync-46", "PD_sync46", "PD_reference"}
    core = list(read_step(ROOT / "cad/step/ZL80_R52_core_review.step"))
    replaced = {
        name for name, _ in core
        if name.split("_", 2)[1] in board_proxies
        or name.split("_", 2)[-1] in detector_proxies
    }
    adf = [
        (name, shape)
        for name, shape in read_step(ROOT / "ZL80_ADF50_V04/cad/ADF50_V04_envelope.step")
        if not name.startswith("REF_")
    ]
    context = [
        (name, shape, shape.BoundingBox())
        for name, shape in core + adf if name not in replaced
    ]
    shift_y = json.loads((ROOT / "engineering/parameters.json").read_text())[
        "collector_guide_r52"
    ]["pmt_shift_y_vs_r5"]

    def align(objects, offset):
        return [
            (name, shape.translate((0, offset, 0))) if name.startswith("B01_")
            else (name, shape)
            for name, shape in objects
        ]

    boards = list(read_step(G4 / "ZL80_G4_4Boards_Installed.step"))
    corridors = list(read_step(G4 / "ZL80_G4_Connector_Keepouts.step"))
    evidence = {
        "scope": "Nominal STEP bodies and provisional mating corridors versus R5.2 core and ADF envelopes. Excludes case, detailed ADF, harnesses, tolerances and new B01 artwork.",
        "volume_threshold_mm3": MIN_VOLUME,
        "boards_and_components": len(boards),
        "context_objects": len(context),
        "removed_duplicate_proxies": sorted(
            "_".join(name.split("_", 2)[:2]) if name.split("_", 2)[1] in board_proxies
            else name for name in replaced
        ),
        "b01_y_shift_mm": shift_y,
        "as_delivered_bodies": intersections(boards, context),
        "aligned_bodies": intersections(align(boards, shift_y), context),
        "aligned_mating_corridors": intersections(align(corridors, shift_y), context),
    }
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
