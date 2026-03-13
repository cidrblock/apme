"""Risk annotator loader and task analysis for Ansible run contexts."""

from __future__ import annotations

import argparse
import json
from typing import cast

import apme_engine.engine.logger as logger
from apme_engine.engine.annotators.risk_annotator_base import RiskAnnotator

from .models import AnsibleRunContext, RunTarget, TaskCall, TaskCallsInTree
from .utils import load_classes_in_dir

annotator_cache: list[RiskAnnotator] = []


def load_annotators(ctx: AnsibleRunContext | None = None) -> list[RiskAnnotator]:
    """Load and cache risk annotator instances from the annotators directory.

    Discovers RiskAnnotator subclasses in the annotators package, instantiates
    each with the provided context, and caches the result for reuse.

    Args:
        ctx: Optional Ansible run context passed to annotator constructors.

    Returns:
        List of instantiated RiskAnnotator instances.

    Raises:
        ValueError: If any annotator fails to instantiate.
    """
    global annotator_cache

    if annotator_cache:
        return annotator_cache

    _annotator_classes, _ = load_classes_in_dir("annotators", RiskAnnotator, __file__)
    _annotators: list[RiskAnnotator] = []
    for a in _annotator_classes:
        try:
            _annotator = cast(type[RiskAnnotator], a)(context=ctx)
            _annotators.append(_annotator)
        except Exception as err:
            raise ValueError(f"failed to load an annotator: {a}") from err
    annotator_cache = _annotators
    return _annotators


def load_taskcalls_in_trees(path: str) -> list[TaskCallsInTree]:
    """Load TaskCallsInTree objects from a newline-delimited JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        List of TaskCallsInTree instances.

    Raises:
        ValueError: If file cannot be read or parsed.
    """
    taskcalls_in_trees: list[TaskCallsInTree] = []
    try:
        with open(path) as file:
            for line in file:
                taskcalls_in_tree = cast(TaskCallsInTree, TaskCallsInTree.from_json(line))
                taskcalls_in_trees.append(taskcalls_in_tree)
    except Exception as e:
        raise ValueError(f"failed to load the json file {path} {e}") from e
    return taskcalls_in_trees


def analyze(contexts: list[AnsibleRunContext]) -> list[AnsibleRunContext]:
    """Run risk annotators on all tasks in the given run contexts.

    For each task in each context, finds a matching enabled annotator, runs it,
    and appends its annotations to the task. Modifies contexts in place.

    Args:
        contexts: List of AnsibleRunContext objects containing tasks.

    Returns:
        The same contexts with annotations added to tasks.
    """
    num = len(contexts)
    for i, ctx in enumerate(contexts):
        if not isinstance(ctx, AnsibleRunContext):
            continue
        for _j, t in enumerate(ctx.tasks):
            if not isinstance(t, TaskCall):
                continue
            annotator = None
            _annotators = load_annotators(ctx)
            for ax in _annotators:
                if not ax.enabled:
                    continue
                if ax.match(task=t):
                    annotator = ax
                    break
            if annotator is None:
                continue
            result = annotator.run(task=t)
            if not result:
                continue
            if result.annotations:
                t.annotations.extend(result.annotations)
        logger.debug(f"analyze() {i + 1}/{num} done")
    return contexts


def main() -> None:
    """CLI entry point: load taskcalls, run analysis, and write results to JSON."""
    parser = argparse.ArgumentParser(
        prog="analyze.py",
        description="analyze tasks",
        epilog="end",
        add_help=True,
    )

    parser.add_argument(
        "-i",
        "--input",
        default="",
        help="path to the input json (taskcalls_in_trees.json)",
    )
    parser.add_argument("-o", "--output", default="", help="path to the output json")

    args = parser.parse_args()

    taskcalls_in_trees = load_taskcalls_in_trees(args.input)
    # Convert to AnsibleRunContext for analyze, then back to TaskCallsInTree for output
    contexts = [
        AnsibleRunContext.from_targets(
            targets=cast(list[RunTarget], tct.taskcalls),
            root_key=tct.root_key,
        )
        for tct in taskcalls_in_trees
    ]
    analyzed_contexts = analyze(contexts)
    # Update taskcalls_in_trees with annotated tasks from analyzed_contexts
    for tct, ctx in zip(taskcalls_in_trees, analyzed_contexts, strict=False):
        for i, tc in enumerate(ctx.taskcalls):
            if i < len(tct.taskcalls):
                tct.taskcalls[i] = cast(TaskCall, tc)

    if args.output != "":
        lines = [json.dumps(single_tree_data) for single_tree_data in taskcalls_in_trees]
        with open(args.output, mode="w") as file:
            file.write("\n".join(lines))


if __name__ == "__main__":
    main()
