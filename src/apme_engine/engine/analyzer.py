import argparse
import json

import apme_engine.engine.logger as logger
from apme_engine.engine.annotators.risk_annotator_base import RiskAnnotator

from .models import AnsibleRunContext, TaskCallsInTree
from .utils import load_classes_in_dir

annotator_cache = []


def load_annotators(ctx: AnsibleRunContext = None):
    global annotator_cache

    if annotator_cache:
        return annotator_cache

    _annotator_classes, _ = load_classes_in_dir("annotators", RiskAnnotator, __file__)
    _annotators = []
    for a in _annotator_classes:
        try:
            _annotator = a(context=ctx)
            _annotators.append(_annotator)
        except Exception as err:
            raise ValueError(f"failed to load an annotator: {a}") from err
    annotator_cache = _annotators
    return _annotators


def load_taskcalls_in_trees(path: str) -> list[TaskCallsInTree]:
    taskcalls_in_trees = []
    try:
        with open(path) as file:
            for line in file:
                taskcalls_in_tree = TaskCallsInTree.from_json(line)
                taskcalls_in_trees.append(taskcalls_in_tree)
    except Exception as e:
        raise ValueError(f"failed to load the json file {path} {e}") from e
    return taskcalls_in_trees


def analyze(contexts: list[AnsibleRunContext]):
    num = len(contexts)
    for i, ctx in enumerate(contexts):
        if not isinstance(ctx, AnsibleRunContext):
            continue
        for _j, t in enumerate(ctx.tasks):
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


def main():
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
    taskcalls_in_trees = analyze(taskcalls_in_trees)

    if args.output != "":
        lines = [json.dumps(single_tree_data) for single_tree_data in taskcalls_in_trees]
        with open(args.output, mode="w") as file:
            file.write("\n".join(lines))


if __name__ == "__main__":
    main()
