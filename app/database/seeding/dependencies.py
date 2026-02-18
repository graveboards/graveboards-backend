from .target import SeederTarget

DEPENDENCIES: dict[SeederTarget, set[SeederTarget]] = {
    SeederTarget.USER: set(),
    SeederTarget.BEATMAP: {SeederTarget.USER},
    SeederTarget.QUEUE: {SeederTarget.USER},
    SeederTarget.REQUEST: {SeederTarget.USER, SeederTarget.QUEUE, SeederTarget.BEATMAP}
}
"""Directed acyclic dependency graph between seeder targets.

Each key depends on the set of ``SeederTargets`` listed as its value. This graph defines 
execution constraints for topological ordering.
"""


def resolve_dependencies(targets: set[SeederTarget]) -> list[list[SeederTarget]]:
    """Resolve transitive dependencies and compute execution layers.

    Performs a depth-first traversal to collect all required targets, then groups them
    into topological layers for ordered execution.

    Args:
        targets:
            Initial set of requested ``SeederTargets``.

    Returns:
        A list of execution layers, where each inner list contains ``SeederTarget`` that
        may be executed concurrently.
    """
    resolved: set[SeederTarget] = set()

    def visit(target: SeederTarget):
        if target in resolved:
            return

        for dep in DEPENDENCIES[target]:
            visit(dep)

        resolved.add(target)

    for t in targets:
        visit(t)

    return _topological_layers(resolved)


def _topological_layers(targets: set[SeederTarget]) -> list[list[SeederTarget]]:
    """Perform layered topological sorting on a dependency graph.

    Targets with no remaining dependencies form a layer. Each layer is removed
    iteratively until all nodes are resolved.

    Args:
        targets:
            Set of ``SeederTarget`` to sort.

    Returns:
        Ordered list of dependency-safe execution layers.

    Raises:
        RuntimeError:
            If a circular dependency is detected.
    """
    graph = {t: DEPENDENCIES[t] & targets for t in targets}
    layers: list[list[SeederTarget]] = []

    while graph:
        ready = {t for t, deps in graph.items() if not deps}

        if not ready:
            raise RuntimeError(f"Circular dependency detected in targets: {targets}")

        layers.append(sorted(ready))

        for t in ready:
            del graph[t]

        for deps in graph.values():
            deps.difference_update(ready)

    return layers
