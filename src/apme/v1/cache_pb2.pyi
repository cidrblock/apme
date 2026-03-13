"""Stub for generated cache_pb2 (proto types)."""

class PullGalaxyRequest:
    spec: str
    galaxy_server: str
    def __init__(self, **kwargs: object) -> None: ...

class PullGalaxyResponse:
    def __init__(self, **kwargs: object) -> None: ...

class PullRequirementsRequest:
    requirements_path: str
    galaxy_server: str
    def __init__(self, **kwargs: object) -> None: ...

class PullRequirementsResponse:
    def __init__(self, **kwargs: object) -> None: ...

class CloneOrgRequest:
    org: str
    repos: list[str]
    depth: int
    token: str
    def __init__(self, **kwargs: object) -> None: ...

class CloneOrgResponse:
    def __init__(self, **kwargs: object) -> None: ...
