import subprocess


def test_ragulate_help() -> None:
    result = subprocess.run(["ragulate", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "RAGu-late CLI tool." in result.stdout
