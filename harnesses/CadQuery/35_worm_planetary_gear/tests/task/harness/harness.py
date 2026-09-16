#!/usr/bin/env python3
"""Grade the planetary output stage of the worm/planetary reducer.

This harness implements eight deterministic planetary assembly criteria.
"""

import ast
import math
import sys
from pathlib import Path

# common/ is at the repo root (five levels up in a checkout) or /opt in the
# Harbor verifier container.
sys.path[:0] = [str(p) for p in Path(__file__).resolve().parents[5:6]] + ["/opt"]

from common.harness_base import Harness, compound, load_script, to_shapes


RING_TEETH_CRITERION = "ring teeth equal sun plus twice planet"
PLANET_COUNT_CRITERION = "planet count divides sun plus planet teeth"
PLANET_SPACING_CRITERION = "planets built at equal angular spacing"
OVERALL_RATIO_CRITERION = "overall reduction is 1500:1"
COLLISION_CRITERION = "no two solid bodies collide"
MESHING_CRITERION = "every gear pair meshes"
UNCHANGED_STAGES_CRITERION = "other three stages unchanged"
PARAMETER_DRIVE_CRITERION = "planetary parameters drive the geometry"

ALL_CRITERIA = {
    RING_TEETH_CRITERION: 1,
    PLANET_COUNT_CRITERION: 1,
    PLANET_SPACING_CRITERION: 1,
    OVERALL_RATIO_CRITERION: 1,
    COLLISION_CRITERION: 1,
    MESHING_CRITERION: 1,
    UNCHANGED_STAGES_CRITERION: 1,
    PARAMETER_DRIVE_CRITERION: 1,
}

TARGET_OVERALL_RATIO = 1500.0
OVERALL_RATIO_TOLERANCE = 0.01
PLANET_SPACING_TOLERANCE_DEG = 1.0
PLANET_SIZE_TOLERANCE_FRAC = 0.05
PLANET_ORBIT_TOLERANCE_FRAC = 0.05
MIN_PLANET_ORBIT_TOLERANCE = 0.1
COLLISION_VOLUME_TOLERANCE = 1e-6
MESH_ABS_TOLERANCE = 1e-6
SCALAR_REL_TOLERANCE = 1e-9
SCALAR_ABS_TOLERANCE = 1e-9
GEOMETRY_REL_TOLERANCE = 1e-7
GEOMETRY_ABS_TOLERANCE = 1e-6
PARAMETER_RESPONSE_TOLERANCE = 1e-8
RATIO_ORDER = ("spur", "bevel", "worm", "planetary")
UPSTREAM_GEAR_NAMES = (
    "spur_gear",
    "superng_gear",
    "supernbevelg2_gear",
    "wornnbevel_gear",
    "worm_gear",
    "wheel_gear",
)
PARAMETER_MUTATIONS = {
    "module": lambda value: value * 1.5,
    "sun_teeth": lambda value: value + 6,
    "planet_teeth": lambda value: value + 6,
    "planet_count": lambda value: value + 1,
}
CANONICAL_PARAMETER_NAMES = {
    "module": "MODULE_STAGE45",
    "sun_teeth": "SUN_TEETH",
    "planet_teeth": "PLANET_TEETH",
    "planet_count": "N_PLANETS",
}


class WormPlanetaryGearHarness(Harness):
    WEIGHTS = ALL_CRITERIA

    def build_state(self, candidate_path):
        baseline_path = (
            self.task_dir() / "tests" / "task" / "prompt" / "input.py"
        )
        baseline_namespace, baseline_error = load_script(baseline_path)
        namespace, candidate_error = load_script(candidate_path)
        state = {
            "baseline_error": baseline_error,
            "load_error": candidate_error,
        }
        if baseline_error is not None or candidate_error is not None:
            return state

        from cq_gears import PlanetaryGearset

        gearsets = self._unique_instances(namespace, PlanetaryGearset)
        state["gearsets"] = gearsets
        state["sun_gear"] = baseline_namespace.get("sun_gear")
        state["collisions"] = self._measure_collisions(namespace)
        state["unchanged_stages"] = self._measure_unchanged_stages(
            baseline_namespace, namespace
        )

        if len(gearsets) != 1 or state["sun_gear"] is None:
            return state

        gearset = gearsets[0]
        state["teeth"] = self._measure_teeth(state["sun_gear"], gearset)
        state["planet_angles"] = self._planet_angles(
            namespace, baseline_namespace, gearset
        )
        state.update(self._measure_ratios(namespace, gearset))
        state["meshing"] = self._measure_meshing(namespace, gearset)
        state["parameter_drive"] = self._measure_parameter_drive(
            candidate_path,
            baseline_namespace,
            namespace,
            gearset,
        )
        return state

    @staticmethod
    def _unique_instances(namespace, expected_type):
        """Distinct namespace values of a type, independent of their names."""
        found = []
        seen_ids = set()
        for value in namespace.values():
            if isinstance(value, expected_type) and id(value) not in seen_ids:
                seen_ids.add(id(value))
                found.append(value)
        return found

    @staticmethod
    def _measure_teeth(baseline_sun, gearset):
        """Tooth counts used by the planetary assembly checks."""
        return {
            # The candidate must mesh with the inherited, unchanged sun.
            "sun": int(baseline_sun.z),
            "planet": int(gearset.planet.z),
            "ring": int(gearset.ring.z),
            "n_planets": int(gearset.n_planets),
        }

    @staticmethod
    def _measure_ratios(namespace, gearset):
        """Four stage ratios, or a recorded measurement error."""
        try:
            stage_ratios = {
                "spur": (
                    float(namespace["superng_gear"].z)
                    / float(namespace["spur_gear"].z)
                ),
                "bevel": (
                    float(namespace["wornnbevel_gear"].z)
                    / float(namespace["supernbevelg2_gear"].z)
                ),
                "worm": (
                    float(namespace["wheel_gear"].z)
                    / float(namespace["worm_gear"].n_threads)
                ),
                # Fixed ring, carrier output: reduction = 1 + Zr / Zs.
                "planetary": (
                    1.0
                    + float(gearset.ring.z)
                    / float(namespace["sun_gear"].z)
                ),
            }
        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
            ZeroDivisionError,
        ) as exc:
            return {"ratio_error": f"{type(exc).__name__}: {exc}"}
        return {
            "stage_ratios": stage_ratios,
            "overall_ratio": math.prod(stage_ratios.values()),
        }

    @staticmethod
    def _measure_meshing(namespace, gearset):
        """Evaluate the scalar relationships required for every mesh."""
        try:
            spur = namespace["spur_gear"]
            spur_mate = namespace["superng_gear"]
            bevel = namespace["supernbevelg2_gear"]
            bevel_mate = namespace["wornnbevel_gear"]
            worm = namespace["worm_gear"]
            wheel = namespace["wheel_gear"]
            sun_stub = namespace["sun_gear"]

            module_pairs = {
                "spur": (float(spur.m), float(spur_mate.m)),
                "bevel": (float(bevel.m), float(bevel_mate.m)),
                "worm/wheel": (float(worm.m), float(wheel.m)),
                "sun/planet": (float(sun_stub.m), float(gearset.planet.m)),
                "planet/ring": (float(gearset.planet.m), float(gearset.ring.m)),
            }
            center_distances = {
                "spur": (
                    float(namespace["r_super_pitch"])
                    + float(namespace["r_supernbevel_pitch"]),
                    float(spur.r0) + float(spur_mate.r0),
                ),
                "worm/wheel": (
                    float(namespace["CENTER_DISTANCE"]),
                    float(worm.r0) + float(wheel.r0),
                ),
                "sun/planet": (
                    float(gearset.orbit_r),
                    float(sun_stub.r0) + float(gearset.planet.r0),
                ),
                "planet/ring": (
                    float(gearset.orbit_r),
                    float(gearset.ring.r0) - float(gearset.planet.r0),
                ),
            }
            bevel_cone_sum = float(bevel.gamma_p) + float(bevel_mate.gamma_p)

            gears = {
                "spur": spur,
                "spur mate": spur_mate,
                "bevel": bevel,
                "bevel mate": bevel_mate,
                "worm": worm,
                "wheel": wheel,
                "sun stub": sun_stub,
                "planetary sun": gearset.sun,
                "planet": gearset.planet,
                "ring": gearset.ring,
            }
            clearances = {
                name: (float(gear.clearance), float(gear.backlash))
                for name, gear in gears.items()
            }
            sun_stub_pairs = {
                field: (
                    float(getattr(sun_stub, field)),
                    float(getattr(gearset.sun, field)),
                )
                for field in ("m", "z", "r0", "clearance", "backlash")
            }
        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}

        return {
            "module_pairs": module_pairs,
            "center_distances": center_distances,
            "bevel_cone_sum": bevel_cone_sum,
            "clearances": clearances,
            "sun_stub_pairs": sun_stub_pairs,
        }

    @staticmethod
    def _numeric_scalars(value):
        """Public numeric attributes that define a gear object."""
        try:
            attributes = vars(value)
        except TypeError:
            return {}
        return {
            name: float(attribute)
            for name, attribute in attributes.items()
            if not name.startswith("_")
            and isinstance(attribute, (int, float))
            and not isinstance(attribute, bool)
        }

    @staticmethod
    def _shape_signature(shape):
        """Volume, bounding box, and centroid of one shown object."""
        bbox = shape.BoundingBox()
        center = shape.Center()
        return (
            float(shape.Volume()),
            float(bbox.xmin),
            float(bbox.ymin),
            float(bbox.zmin),
            float(bbox.xmax),
            float(bbox.ymax),
            float(bbox.zmax),
            float(center.x),
            float(center.y),
            float(center.z),
        )

    @staticmethod
    def _signatures_match(left, right):
        return all(
            math.isclose(
                left_value,
                right_value,
                rel_tol=GEOMETRY_REL_TOLERANCE,
                abs_tol=GEOMETRY_ABS_TOLERANCE,
            )
            for left_value, right_value in zip(left, right)
        )

    @classmethod
    def _measure_unchanged_stages(cls, baseline_namespace, namespace):
        """Compare upstream gear scalars and the eight inherited solids."""
        try:
            scalar_changes = []
            for gear_name in UPSTREAM_GEAR_NAMES:
                baseline_gear = baseline_namespace[gear_name]
                candidate_gear = namespace[gear_name]
                baseline_scalars = cls._numeric_scalars(baseline_gear)
                candidate_scalars = cls._numeric_scalars(candidate_gear)

                if type(candidate_gear) is not type(baseline_gear):
                    scalar_changes.append(
                        f"{gear_name} type changed from "
                        f"{type(baseline_gear).__name__} to "
                        f"{type(candidate_gear).__name__}"
                    )
                for field, baseline_value in baseline_scalars.items():
                    candidate_value = candidate_scalars.get(field)
                    if candidate_value is None or not math.isclose(
                        candidate_value,
                        baseline_value,
                        rel_tol=SCALAR_REL_TOLERANCE,
                        abs_tol=SCALAR_ABS_TOLERANCE,
                    ):
                        scalar_changes.append(
                            f"{gear_name}.{field}: "
                            f"{baseline_value:g}->{candidate_value!r}"
                        )

            baseline_shapes = cls._shown_shapes(baseline_namespace)
            candidate_shapes = cls._shown_shapes(namespace)
            remaining_candidates = [
                (name, cls._shape_signature(shape))
                for name, shape in candidate_shapes
            ]
            missing_shapes = []
            for baseline_name, baseline_shape in baseline_shapes:
                baseline_signature = cls._shape_signature(baseline_shape)
                match_index = next(
                    (
                        index
                        for index, (_, candidate_signature) in enumerate(
                            remaining_candidates
                        )
                        if cls._signatures_match(
                            baseline_signature, candidate_signature
                        )
                    ),
                    None,
                )
                if match_index is None:
                    missing_shapes.append(baseline_name)
                else:
                    remaining_candidates.pop(match_index)
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}

        return {
            "scalar_changes": scalar_changes,
            "missing_shapes": missing_shapes,
            "baseline_shape_count": len(baseline_shapes),
            "candidate_shape_count": len(candidate_shapes),
        }

    @staticmethod
    def _literal_assignments(candidate_path):
        """Numeric module-level assignments that load_script can override."""
        source = Path(candidate_path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(candidate_path))
        assignments = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets = [
                    target.id
                    for target in node.targets
                    if isinstance(target, ast.Name)
                ]
                value_node = node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(
                node.target, ast.Name
            ):
                targets = [node.target.id]
                value_node = node.value
            else:
                continue

            try:
                value = ast.literal_eval(value_node)
            except (ValueError, TypeError):
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                for name in targets:
                    assignments.setdefault(name, value)
        return assignments

    @staticmethod
    def _parameter_name_matches(kind, name):
        lowered = name.lower()
        has_planet = "planet" in lowered
        count_words = ("count", "number", "num", "n_planet")
        if kind == "module":
            return "module" in lowered and (
                has_planet or "stage4" in lowered or "stage45" in lowered
            )
        if kind == "sun_teeth":
            return "sun" in lowered and (
                "teeth" in lowered or "tooth" in lowered
            )
        if kind == "planet_teeth":
            return (
                has_planet
                and not any(word in lowered for word in count_words)
                and (
                    "teeth" in lowered
                    or "tooth" in lowered
                    or lowered.startswith("zp_")
                )
            )
        if kind == "planet_count":
            return has_planet and any(word in lowered for word in count_words)
        return False

    @classmethod
    def _find_probe_parameters(cls, candidate_path, gearset):
        assignments = cls._literal_assignments(candidate_path)
        expected_values = {
            "module": float(gearset.sun.m),
            "sun_teeth": int(gearset.sun.z),
            "planet_teeth": int(gearset.planet.z),
            "planet_count": int(gearset.n_planets),
        }
        resolved = {}
        unresolved = {}
        for kind, expected in expected_values.items():
            canonical = CANONICAL_PARAMETER_NAMES[kind]
            if canonical in assignments:
                resolved[kind] = (canonical, assignments[canonical])
                continue

            matches = [
                (name, value)
                for name, value in assignments.items()
                if cls._parameter_name_matches(kind, name)
                and math.isclose(float(value), float(expected), abs_tol=1e-12)
            ]
            if len(matches) == 1:
                resolved[kind] = matches[0]
            else:
                unresolved[kind] = [name for name, _ in matches]
        return resolved, unresolved

    @classmethod
    def _added_shape_indices(cls, baseline_namespace, namespace):
        """Indices of shown candidate objects absent from the frozen model."""
        baseline_signatures = [
            cls._shape_signature(shape)
            for _, shape in cls._shown_shapes(baseline_namespace)
        ]
        candidate_shapes = cls._shown_shapes(namespace)
        unmatched_indices = set(range(len(candidate_shapes)))
        for baseline_signature in baseline_signatures:
            match_index = next(
                (
                    index
                    for index in sorted(unmatched_indices)
                    if cls._signatures_match(
                        baseline_signature,
                        cls._shape_signature(candidate_shapes[index][1]),
                    )
                ),
                None,
            )
            if match_index is not None:
                unmatched_indices.remove(match_index)
        return sorted(unmatched_indices)

    @classmethod
    def _response_signatures(cls, namespace, shown_indices):
        """Volume and extents of the candidate's planetary shown objects."""
        shown_shapes = cls._shown_shapes(namespace)
        if any(index >= len(shown_shapes) for index in shown_indices):
            return None
        signatures = []
        for index in shown_indices:
            shape = shown_shapes[index][1]
            bbox = shape.BoundingBox()
            signatures.append(
                (
                    float(shape.Volume()),
                    float(bbox.xlen),
                    float(bbox.ylen),
                    float(bbox.zlen),
                )
            )
        return signatures

    @staticmethod
    def _maximum_response_change(baseline, mutated):
        if mutated is None or len(baseline) != len(mutated):
            return math.inf
        changes = [
            abs(after - before) / max(abs(before), 1e-12)
            for baseline_signature, mutated_signature in zip(baseline, mutated)
            for before, after in zip(baseline_signature, mutated_signature)
        ]
        return max(changes, default=0.0)

    @classmethod
    def _measure_parameter_drive(
        cls, candidate_path, baseline_namespace, namespace, gearset
    ):
        """Perturb each planetary parameter and observe added geometry."""
        try:
            parameters, unresolved = cls._find_probe_parameters(
                candidate_path, gearset
            )
            shown_indices = cls._added_shape_indices(
                baseline_namespace, namespace
            )
            baseline_signatures = cls._response_signatures(
                namespace, shown_indices
            )
        except (
            AttributeError,
            OSError,
            SyntaxError,
            TypeError,
            ValueError,
        ) as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}

        if not shown_indices:
            return {
                "error": "no added planetary shown objects were found",
                "unresolved": unresolved,
            }

        attempts = {}
        for kind, mutate in PARAMETER_MUTATIONS.items():
            if kind not in parameters:
                attempts[kind] = {
                    "passed": False,
                    "error": "parameter assignment was not resolved",
                }
                continue

            name, old_value = parameters[kind]
            new_value = mutate(old_value)
            mutated_namespace, build_error = load_script(
                candidate_path, overrides={name: new_value}
            )
            attempt = {
                "name": name,
                "old": old_value,
                "new": new_value,
                "build_ok": build_error is None,
            }
            if build_error is not None:
                attempt.update(
                    passed=True,
                    error=f"{type(build_error).__name__}: {build_error}",
                )
            else:
                mutated_signatures = cls._response_signatures(
                    mutated_namespace, shown_indices
                )
                change = cls._maximum_response_change(
                    baseline_signatures, mutated_signatures
                )
                attempt.update(
                    passed=change > PARAMETER_RESPONSE_TOLERANCE,
                    maximum_relative_change=change,
                )
            attempts[kind] = attempt

        return {
            "attempts": attempts,
            "unresolved": unresolved,
            "planetary_object_count": len(shown_indices),
        }

    @staticmethod
    def _shown_shapes(namespace):
        """Shown geometry collapsed to one shape per show_object call."""
        result = []
        for index, shown in enumerate(namespace.get("__shown__", ())):
            shapes = to_shapes(shown)
            if shapes:
                result.append((f"shown[{index}]", compound(shapes)))
        return result

    @staticmethod
    def _bbox_overlap_extents(bbox_a, bbox_b):
        return (
            min(bbox_a.xmax, bbox_b.xmax) - max(bbox_a.xmin, bbox_b.xmin),
            min(bbox_a.ymax, bbox_b.ymax) - max(bbox_a.ymin, bbox_b.ymin),
            min(bbox_a.zmax, bbox_b.zmax) - max(bbox_a.zmin, bbox_b.zmin),
        )

    @staticmethod
    def _measure_collisions(namespace):
        """Measure overlap volume for every bbox-overlapping shown object."""
        shown_shapes = WormPlanetaryGearHarness._shown_shapes(namespace)

        checked_pairs = 0
        overlaps = []
        unresolved = []
        for i, (name_a, shape_a) in enumerate(shown_shapes):
            bbox_a = shape_a.BoundingBox()
            for name_b, shape_b in shown_shapes[i + 1:]:
                bbox_b = shape_b.BoundingBox()
                overlap_extents = WormPlanetaryGearHarness._bbox_overlap_extents(
                    bbox_a, bbox_b
                )
                # A zero extent is bounding-box contact, which cannot contain
                # positive overlap volume and therefore is not charged.
                if any(extent <= 0.0 for extent in overlap_extents):
                    continue

                checked_pairs += 1
                try:
                    common_volume = float(shape_a.intersect(shape_b).Volume())
                except Exception as exc:
                    unresolved.append(
                        f"{name_a}/{name_b}: {type(exc).__name__}: {exc}"
                    )
                    continue
                if common_volume > COLLISION_VOLUME_TOLERANCE:
                    overlaps.append(
                        {"pair": f"{name_a}/{name_b}", "volume": common_volume}
                    )

        return {
            "shown_count": len(shown_shapes),
            "checked_pairs": checked_pairs,
            "overlaps": overlaps,
            "unresolved": unresolved,
        }

    @staticmethod
    def _planet_angles(namespace, baseline_namespace, gearset):
        """Angles of planet-like shown solids about the planetary axis.

        Planet variables may be renamed or merged into a multi-solid
        Workplane. Identify the individual solids by their measured XY tip
        diameter and orbit radius instead of by a namespace name.
        """
        axis_offset = (
            namespace.get("worm_wheel_final_offset")
            or baseline_namespace.get("worm_wheel_final_offset")
        )
        if axis_offset is None:
            return []
        axis_x, axis_y = float(axis_offset[0]), float(axis_offset[1])

        tip_diameter = float(gearset.planet.ra) * 2.0
        orbit_radius = float(gearset.orbit_r)
        size_tolerance = tip_diameter * PLANET_SIZE_TOLERANCE_FRAC
        orbit_tolerance = max(
            orbit_radius * PLANET_ORBIT_TOLERANCE_FRAC,
            MIN_PLANET_ORBIT_TOLERANCE,
        )

        planets = []
        seen = set()
        for shown in namespace.get("__shown__", ()):
            for shape in to_shapes(shown):
                for solid in shape.Solids():
                    bb = solid.BoundingBox()
                    center = solid.Center()
                    radius = math.hypot(center.x - axis_x, center.y - axis_y)
                    if (
                        abs(bb.xlen - tip_diameter) <= size_tolerance
                        and abs(bb.ylen - tip_diameter) <= size_tolerance
                        and abs(radius - orbit_radius) <= orbit_tolerance
                    ):
                        signature = (
                            round(center.x, 6),
                            round(center.y, 6),
                            round(center.z, 6),
                        )
                        if signature not in seen:
                            seen.add(signature)
                            planets.append(center)

        return sorted(
            math.degrees(math.atan2(p.y - axis_y, p.x - axis_x)) % 360.0
            for p in planets
        )

    @staticmethod
    def _check_ring_teeth(state):
        teeth = state.get("teeth")
        passed = bool(
            teeth
            and teeth["ring"] == teeth["sun"] + 2 * teeth["planet"]
        )
        if state.get("baseline_error") is not None:
            detail = f"frozen baseline did not build: {state['baseline_error']}"
        elif state.get("load_error") is not None:
            detail = f"candidate did not build: {state['load_error']}"
        elif len(state.get("gearsets", ())) != 1:
            detail = (
                "expected exactly one PlanetaryGearset, found "
                f"{len(state.get('gearsets', ()))}"
            )
        elif teeth is None:
            detail = "the inherited sun_gear or gear tooth data is unavailable"
        else:
            detail = (
                f"ring={teeth['ring']}, sun={teeth['sun']}, "
                f"planet={teeth['planet']}, expected ring="
                f"{teeth['sun'] + 2 * teeth['planet']}"
            )
        return passed, detail

    @staticmethod
    def _check_planet_count(state):
        teeth = state.get("teeth")
        passed = bool(
            teeth
            and teeth["n_planets"] > 0
            and (teeth["sun"] + teeth["planet"]) % teeth["n_planets"] == 0
        )
        if teeth is None:
            detail = "gear tooth data is unavailable"
        elif teeth["n_planets"] <= 0:
            detail = (
                f"invalid planet count: n_planets={teeth['n_planets']}"
            )
        else:
            dividend = teeth["sun"] + teeth["planet"]
            remainder = dividend % teeth["n_planets"]
            detail = (
                f"sun+planet={dividend}, n_planets={teeth['n_planets']}, "
                f"remainder={remainder}"
            )
        return passed, detail

    @staticmethod
    def _check_planet_spacing(state):
        teeth = state.get("teeth")
        angles = state.get("planet_angles", [])
        gap_errors = []
        if teeth and len(angles) == teeth["n_planets"] and angles:
            gaps = [
                (angles[(i + 1) % len(angles)] - angles[i]) % 360.0
                for i in range(len(angles))
            ]
            expected_gap = 360.0 / teeth["n_planets"]
            gap_errors = [abs(gap - expected_gap) for gap in gaps]
        passed = bool(
            gap_errors
            and max(gap_errors) <= PLANET_SPACING_TOLERANCE_DEG
        )

        if not teeth:
            detail = "gear tooth data is unavailable"
        elif len(angles) != teeth["n_planets"]:
            detail = (
                f"expected {teeth['n_planets']} planet solids, found "
                f"{len(angles)}; angles={angles}"
            )
        else:
            detail = (
                f"angles={[round(a, 3) for a in angles]}, "
                f"gap errors={[round(e, 3) for e in gap_errors]} deg, "
                f"allowed <= {PLANET_SPACING_TOLERANCE_DEG:g} deg"
            )
        return passed, detail

    @staticmethod
    def _check_overall_ratio(state):
        overall_ratio = state.get("overall_ratio")
        relative_error = (
            abs(overall_ratio - TARGET_OVERALL_RATIO) / TARGET_OVERALL_RATIO
            if overall_ratio is not None
            else None
        )
        passed = bool(
            relative_error is not None
            and relative_error <= OVERALL_RATIO_TOLERANCE
        )
        if state.get("ratio_error"):
            detail = f"could not calculate ratio: {state['ratio_error']}"
        elif overall_ratio is None:
            detail = "gear ratio data is unavailable"
        else:
            ratios = state["stage_ratios"]
            detail = (
                "stages="
                f"{[round(ratios[name], 6) for name in RATIO_ORDER]}, "
                f"overall={overall_ratio:.6f}:1, "
                f"relative error={relative_error * 100:.4f}%, allowed <= "
                f"{OVERALL_RATIO_TOLERANCE * 100:g}%"
            )
        return passed, detail

    @staticmethod
    def _check_collisions(state):
        measurement = state.get("collisions")
        if measurement is None:
            return False, "collision measurement is unavailable"

        overlaps = measurement["overlaps"]
        unresolved = measurement["unresolved"]
        passed = not overlaps and not unresolved
        if unresolved:
            detail = (
                f"{len(unresolved)} boolean operation(s) unresolved: "
                + "; ".join(unresolved)
            )
        elif overlaps:
            formatted = "; ".join(
                f"{item['pair']}={item['volume']:.6g} mm^3"
                for item in overlaps
            )
            detail = f"{len(overlaps)} interpenetrating pair(s): {formatted}"
        else:
            detail = (
                f"no positive common volume across "
                f"{measurement['checked_pairs']} bbox-overlapping pair(s) "
                f"among {measurement['shown_count']} shown object(s)"
            )
        return passed, detail

    @staticmethod
    def _check_meshing(state):
        measurement = state.get("meshing")
        if measurement is None:
            return False, "meshing measurement is unavailable"
        if measurement.get("error"):
            return False, f"could not measure gear meshes: {measurement['error']}"

        failures = []
        for name, (left, right) in measurement["module_pairs"].items():
            if abs(left - right) > MESH_ABS_TOLERANCE:
                failures.append(f"{name} module {left:g}!={right:g}")

        for name, (actual, expected) in measurement["center_distances"].items():
            if abs(actual - expected) > MESH_ABS_TOLERANCE:
                failures.append(
                    f"{name} centre distance {actual:g}!={expected:g}"
                )

        cone_sum_deg = math.degrees(measurement["bevel_cone_sum"])
        if (
            abs(measurement["bevel_cone_sum"] - math.pi / 2.0)
            > MESH_ABS_TOLERANCE
        ):
            failures.append(f"bevel cone-angle sum {cone_sum_deg:g} deg!=90 deg")

        for name, (clearance, backlash) in measurement["clearances"].items():
            if clearance <= 0.0:
                failures.append(f"{name} clearance {clearance:g} is not positive")
            if backlash <= 0.0:
                failures.append(f"{name} backlash {backlash:g} is not positive")

        for field, (stub_value, planetary_value) in measurement[
            "sun_stub_pairs"
        ].items():
            if abs(stub_value - planetary_value) > MESH_ABS_TOLERANCE:
                failures.append(
                    f"sun stub {field} {stub_value:g}!={planetary_value:g}"
                )

        if failures:
            return False, "; ".join(failures)
        return (
            True,
            "all modules and centre distances match; bevel cone angles sum "
            f"to {cone_sum_deg:.6f} deg; clearance/backlash are positive; "
            "sun stub matches the planetary sun",
        )

    @staticmethod
    def _check_unchanged_stages(state):
        measurement = state.get("unchanged_stages")
        if measurement is None:
            return False, "upstream-stage comparison is unavailable"
        if measurement.get("error"):
            return (
                False,
                "could not compare upstream stages: " + measurement["error"],
            )

        scalar_changes = measurement["scalar_changes"]
        missing_shapes = measurement["missing_shapes"]
        passed = not scalar_changes and not missing_shapes
        details = []
        if scalar_changes:
            details.append("changed gear scalars: " + "; ".join(scalar_changes))
        if missing_shapes:
            details.append(
                "missing or changed inherited geometry: "
                + ", ".join(missing_shapes)
            )
        if not details:
            details.append(
                f"all {len(UPSTREAM_GEAR_NAMES)} upstream gear objects and "
                f"{measurement['baseline_shape_count']} inherited shown "
                "objects match the frozen baseline"
            )
        return passed, "; ".join(details)

    @staticmethod
    def _check_parameter_drive(state):
        measurement = state.get("parameter_drive")
        if measurement is None:
            return False, "parameter-drive measurement is unavailable"
        if measurement.get("error"):
            return False, "could not probe parameters: " + measurement["error"]

        attempts = measurement["attempts"]
        passed = len(attempts) == len(PARAMETER_MUTATIONS) and all(
            attempt.get("passed", False) for attempt in attempts.values()
        )
        details = []
        for kind in PARAMETER_MUTATIONS:
            attempt = attempts[kind]
            name = attempt.get("name", kind)
            if not attempt.get("build_ok", False):
                if attempt.get("passed", False):
                    result = "build reacted with an error"
                else:
                    result = attempt.get("error", "probe failed")
            else:
                change = attempt.get("maximum_relative_change", 0.0)
                result = f"maximum relative change={change:.6g}"
            details.append(f"{name}: {result}")

        return passed, (
            f"watched {measurement['planetary_object_count']} planetary "
            "shown object(s); " + "; ".join(details)
        )

    def checks(self, state):
        check_functions = {
            RING_TEETH_CRITERION: self._check_ring_teeth,
            PLANET_COUNT_CRITERION: self._check_planet_count,
            PLANET_SPACING_CRITERION: self._check_planet_spacing,
            OVERALL_RATIO_CRITERION: self._check_overall_ratio,
            COLLISION_CRITERION: self._check_collisions,
            MESHING_CRITERION: self._check_meshing,
            UNCHANGED_STAGES_CRITERION: self._check_unchanged_stages,
            PARAMETER_DRIVE_CRITERION: self._check_parameter_drive,
        }
        results = {}
        for criterion, check_function in check_functions.items():
            score, detail = check_function(state)
            results[criterion] = score
            print(f"{criterion}: {detail}", file=sys.stderr)

        return results


main = WormPlanetaryGearHarness.as_main()


if __name__ == "__main__":
    WormPlanetaryGearHarness.cli()
