from pathlib import Path

from tools.legacy_scanner import scan_legacy_assets


def test_scan_legacy_assets_lists_expected_files(tmp_path: Path):
    # Use real project for existing assets to avoid brittle fixtures
    project_root = Path.cwd()
    result = scan_legacy_assets(str(project_root))

    # Basic expectations: legacy templates and scripts should be detected
    assert any(p.startswith("templates/") for p in result.templates)
    assert any(p.startswith("static/js/") and p.endswith("_scripts_v2.js") for p in result.legacy_v2_scripts)
    assert any(p.startswith("static/js/Legacy/") for p in result.legacy_dir_scripts)
    assert any(p.startswith("static/js/external/") for p in result.external_scripts)

    # Routes presence should reflect current codebase
    assert result.routes.has_publishing_render is True
    assert result.routes.has_mstpid_endpoint is True


