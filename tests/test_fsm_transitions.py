import unittest

from resume_validation.fsm_controller import FSMController, FSMObservation, Phase
from resume_validation.fsm_trajectory import CommandReference, ReferenceTrajectory


class FSMTest(unittest.TestCase):
    def test_stable_clear_success_requires_debounce(self):
        reference = CommandReference(0.0, {}, {}, 0, "")
        controller = FSMController(ReferenceTrajectory(0.05, 10.0, (reference,)), debounce_steps=2)
        obs = FSMObservation(1.0, 1.0, 4, 0, True, True)
        self.assertNotEqual(controller.step(obs).phase, Phase.SUCCESS)
        self.assertEqual(controller.step(obs).phase, Phase.SUCCESS)

    def test_approach_cannot_advance_without_debounced_contact(self):
        reference = CommandReference(0.0, {}, {}, 0, "")
        controller = FSMController(ReferenceTrajectory(0.05, 10.0, (reference,)), debounce_steps=2)
        controller.phase = Phase.APPROACH
        no_contact = FSMObservation(3.0, 0.1, 0, 4, False, False)
        self.assertEqual(controller.step(no_contact).phase, Phase.APPROACH)
        contact = FSMObservation(3.0, 0.0, 0, 4, False, False, front_contact=True)
        self.assertEqual(controller.step(contact).phase, Phase.APPROACH)
        self.assertEqual(controller.step(contact).phase, Phase.FIRST_CONTACT_CONFIRM)


if __name__ == "__main__":
    unittest.main()
