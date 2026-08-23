import unittest

from resume_validation.paths import REFERENCE_REPLAY_ROOT
from resume_validation.replay_loader import flatten_events, load_jsonl, load_replay, playback_scaled_event


class ReplayLoaderTest(unittest.TestCase):
    def test_real_replays_parse(self):
        counts = {}
        dispatch_counts = {}
        for height in (5, 10):
            path = REFERENCE_REPLAY_ROOT / "saved_height_steps" / f"height_{height:02d}cm" / "accepted_steps.jsonl"
            steps = load_replay(path)
            counts[height] = len(steps)
            dispatch_counts[height] = sum(
                len(event.playback_commands) for step in steps for event in step.events
            )
            self.assertTrue(all(step.height_m == height / 100.0 for step in steps))
        self.assertEqual(counts, {5: 35, 10: 18})
        self.assertEqual(dispatch_counts, {5: 269, 10: 101})

    def test_preserve_distance_scaling(self):
        event = load_replay(
            REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        )[0].events[0]
        scaled = playback_scaled_event(event, 2.0, True, 2.0943951023931953)
        self.assertAlmostEqual(scaled.time_s, event.time_s / 2.0)

    def test_idle_cap_compresses_event_times_monotonically(self):
        steps = load_replay(
            REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        )
        events = flatten_events(steps, max_idle_gap_s=1.0)
        self.assertTrue(all(a.time_s <= b.time_s for a, b in zip(events, events[1:])))
        self.assertLessEqual(events[-1].time_s, len(steps) + len(events))

    def test_fast_timing_caps_each_gap_and_shifts_first_event_to_zero(self):
        steps = load_replay(
            REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        )
        events = flatten_events(steps[:1], max_idle_gap_s=1.0)
        self.assertEqual(events[0].time_s, 0.0)
        # Raw gap 8.859 s between wheel start and stop is capped to 1 s.
        self.assertAlmostEqual(events[1].time_s, 1.0)

    def test_fsm_timing_preserves_nonzero_wheel_interval(self):
        steps = load_replay(
            REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        )
        events = flatten_events(
            steps[:1],
            max_idle_gap_s=1.0,
            preserve_wheel_active_gaps=True,
        )
        # The first event starts a 0.3 rad/s hold. Its full duration must
        # survive idle compression so commanded wheel travel is unchanged.
        raw_gap = steps[0].events[1].time_s - steps[0].events[0].time_s
        self.assertAlmostEqual(events[1].time_s - events[0].time_s, raw_gap)

    def test_fsm_timing_preserves_full_replay_wheel_angle(self):
        wheel_names = (
            "front_left_ankle",
            "front_right_ankle",
            "rear_left_ankle",
            "rear_right_ankle",
        )

        def integrated_angle(events, end_time):
            total = {name: 0.0 for name in wheel_names}
            for index, event in enumerate(events):
                next_time = events[index + 1].time_s if index + 1 < len(events) else end_time
                for name in wheel_names:
                    total[name] += event.wheel_targets_rad_s[name] * (next_time - event.time_s)
            return total

        for height in (5, 10):
            steps = load_replay(
                REFERENCE_REPLAY_ROOT / "saved_height_steps" / f"height_{height:02d}cm" / "accepted_steps.jsonl"
            )
            raw = flatten_events(steps)
            compressed = flatten_events(
                steps,
                max_idle_gap_s=1.0,
                preserve_wheel_active_gaps=True,
            )
            raw_angle = integrated_angle(raw, sum(step.duration_s for step in steps))
            compressed_angle = integrated_angle(compressed, compressed[-1].time_s + 0.05)
            for name in wheel_names:
                self.assertAlmostEqual(compressed_angle[name], raw_angle[name], places=10)

    def test_raw_timing_keeps_original_step_offsets(self):
        steps = load_replay(
            REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        )
        events = flatten_events(steps[:2])
        second_step_first = next(event for event in events if event.step_index == steps[1].index)
        self.assertAlmostEqual(second_step_first.time_s, steps[0].duration_s + steps[1].events[0].time_s)

    def test_commands_are_applied_at_their_own_event_not_from_stale_snapshots(self):
        steps = load_replay(
            REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        )
        # Late legacy events contain stale command_state_after snapshots:
        # event 155 says wheel all 0.3 but its snapshot still says zero.
        wheel_start, wheel_stop = steps[33].events
        self.assertEqual(wheel_start.playback_commands, ("wheel all 0.3",))
        self.assertTrue(all(value == 0.3 for value in wheel_start.wheel_targets_rad_s.values()))
        self.assertTrue(all(value == 0.0 for value in wheel_stop.wheel_targets_rad_s.values()))

    def test_expanded_batch_commands_reconstruct_full_post_event_state(self):
        steps = load_replay(
            REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        )
        batch = steps[6].events[0]
        self.assertEqual(len(batch.playback_commands), 12)
        self.assertAlmostEqual(batch.servo_targets_deg["front_left_hip"], -0.7)
        self.assertAlmostEqual(batch.wheel_targets_rad_s["front_left_ankle"], -2.09)
        self.assertAlmostEqual(batch.wheel_targets_rad_s["rear_left_ankle"], 1.88)

    def test_each_reconstructed_step_finishes_at_logged_step_state(self):
        path = REFERENCE_REPLAY_ROOT / "saved_height_steps" / "height_05cm" / "accepted_steps.jsonl"
        rows = load_jsonl(path)
        steps = load_replay(path)
        for row, step in zip(rows, steps):
            if not step.events:
                continue
            expected = row["command_state_after"]
            self.assertEqual(step.events[-1].servo_targets_deg, expected["servos"])
            self.assertEqual(step.events[-1].wheel_targets_rad_s, expected["wheels"])


if __name__ == "__main__":
    unittest.main()
