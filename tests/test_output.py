from __future__ import annotations

from io import StringIO

from camera_vision.config import OutputMode
from camera_vision.output import Reporter


def test_human_output_uses_delimiters() -> None:
    stdout = StringIO()
    stderr = StringIO()
    reporter = Reporter(OutputMode.HUMAN, stdout=stdout, stderr=stderr)

    reporter.status("Starting")
    reporter.description("A desk and a chair.")
    reporter.error("Model unavailable")

    assert "--- Model description ---" in stdout.getvalue()
    assert "A desk and a chair." in stdout.getvalue()
    assert "Starting" not in stdout.getvalue()
    assert stderr.getvalue() == "Starting\nError: Model unavailable\n"


def test_description_output_is_one_clean_line() -> None:
    stdout = StringIO()
    stderr = StringIO()
    reporter = Reporter(OutputMode.DESCRIPTION, stdout=stdout, stderr=stderr)

    reporter.status("Analyzing")
    reporter.description("A room\nwith   two chairs.")
    reporter.error("Later failure")

    assert stdout.getvalue() == "A room with two chairs.\n"
    assert stderr.getvalue() == "Analyzing\nError: Later failure\n"
