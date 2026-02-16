from .target import SeederTarget

DEPENDENCIES: dict[SeederTarget, set[SeederTarget]] = {
    SeederTarget.USER: set(),
    SeederTarget.BEATMAP: {SeederTarget.USER},
    SeederTarget.QUEUE: {SeederTarget.USER},
    SeederTarget.REQUEST: {SeederTarget.USER, SeederTarget.QUEUE, SeederTarget.BEATMAP}
}


def resolve_dependencies(targets: set[SeederTarget]) -> list[list[SeederTarget]]:
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
