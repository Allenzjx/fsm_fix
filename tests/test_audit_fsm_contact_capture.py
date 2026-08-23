from resume_validation.audit_fsm_contact_capture import _longest_true_run


def test_longest_true_run_uses_sample_dwell_and_breaks_on_false() -> None:
    samples = [
        (0.00, False),
        (0.01, True),
        (0.02, True),
        (0.03, False),
        (0.04, True),
        (0.05, True),
        (0.06, True),
    ]
    result = _longest_true_run(samples, 0.01)
    assert result == {
        "sample_count": 3,
        "start_time_s": 0.04,
        "end_time_s": 0.06,
        "duration_s": 0.03,
    }


def test_longest_true_run_breaks_on_timestamp_gap() -> None:
    result = _longest_true_run(
        [(1.00, True), (1.01, True), (1.10, True)],
        0.01,
    )
    assert result["sample_count"] == 2
    assert result["duration_s"] == 0.02
