from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


LEGACY_V2_GLOB = "static/js/*_scripts_v2.js"
LEGACY_DIR_GLOB = "static/js/Legacy/**/*"
TEMPLATES_GLOB = "templates/*.html"
EXTERNAL_GLOB = "static/js/external/**"


@dataclass
class RouteScan:
    has_publishing_render: bool
    has_mstpid_endpoint: bool
    matched_lines: List[str]


@dataclass
class LegacyScanResult:
    templates: List[str]
    legacy_v2_scripts: List[str]
    legacy_dir_scripts: List[str]
    external_scripts: List[str]
    routes: RouteScan

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        # Normalize path separators for consistency
        for key in [
            "templates",
            "legacy_v2_scripts",
            "legacy_dir_scripts",
            "external_scripts",
        ]:
            data[key] = [p.replace("\\", "/") for p in data[key]]
        return data


def _glob(root: Path, pattern: str) -> List[str]:
    return [str(p.relative_to(root)).replace("\\", "/") for p in root.glob(pattern)]


def _scan_routes(root: Path) -> RouteScan:
    main_py = root / "main.py"
    matched: List[str] = []
    has_pub = False
    has_mst = False

    if main_py.exists():
        content = main_py.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in content:
            if (
                '@app.get("/publishing-render/' in line
                or '@app.post("/publishing-render/' in line
            ):
                has_pub = True
                matched.append(line.strip())
            if (
                '@app.get("/api/v1/o/form/master/' in line
                or '@app.post("/api/v1/o/form/master/' in line
            ):
                has_mst = True
                matched.append(line.strip())

    return RouteScan(
        has_publishing_render=has_pub,
        has_mstpid_endpoint=has_mst,
        matched_lines=matched,
    )


def scan_legacy_assets(project_root: Optional[str] = None) -> LegacyScanResult:
    """
    Scan repository for legacy assets and mixed publishing routes.

    Returns a LegacyScanResult with relative paths from project root.
    """
    root = Path(project_root) if project_root else Path.cwd()

    templates = _glob(root, TEMPLATES_GLOB)
    legacy_v2 = _glob(root, LEGACY_V2_GLOB)
    legacy_dir = _glob(root, LEGACY_DIR_GLOB)
    external = _glob(root, EXTERNAL_GLOB)
    routes = _scan_routes(root)

    return LegacyScanResult(
        templates=templates,
        legacy_v2_scripts=legacy_v2,
        legacy_dir_scripts=legacy_dir,
        external_scripts=external,
        routes=routes,
    )


def main() -> None:
    result = scan_legacy_assets()
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
