import subprocess
import sys


def assert_import_success(result: subprocess.CompletedProcess) -> None:
    """Assert subprocess import succeeded, allowing lancedb/pyarrow shutdown crash (exit 134)."""
    if result.returncode == 0:
        return
    if result.returncode == 134 and "PyGILState_Release" in (result.stderr or ""):
        return
    raise AssertionError(
        f"Expected import to succeed (0 or 134+PyGILState_Release), got {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}\n"
    )


def test_import_scripts_db_module() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.db"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert_import_success(result)

