import unittest

from resume_validation.contact_processing import Contact, ContactClass, classify_contact, is_valid_support


class ContactClassificationTest(unittest.TestCase):
    def test_riser_horizontal_contact_is_not_support(self):
        contact = Contact("front_left_wheel", (1.0, 0.0, 0.04), (10.0, 0.0, 0.1), "Obstacle")
        kind = classify_contact(
            contact,
            obstacle_top_z=0.1,
            obstacle_front_x=1.0,
            top_tolerance_m=0.01,
            riser_tolerance_m=0.01,
            min_upward_force_n=1.0,
        )
        self.assertEqual(kind, ContactClass.STEP_RISER)
        self.assertFalse(is_valid_support(kind, contact.upward_force, 1.0))

    def test_top_contact_is_support(self):
        contact = Contact("front_left_wheel", (1.1, 0.0, 0.1), (0.0, 0.0, 5.0), "Obstacle")
        kind = classify_contact(
            contact,
            obstacle_top_z=0.1,
            obstacle_front_x=1.0,
            top_tolerance_m=0.01,
            riser_tolerance_m=0.01,
            min_upward_force_n=1.0,
        )
        self.assertEqual(kind, ContactClass.STEP_TOP)
        self.assertTrue(is_valid_support(kind, 5.0, 1.0))

    def test_ambiguous_sensor_label_still_excludes_riser(self):
        contact = Contact("front_left_wheel", (1.0, 0.0, 0.04), (0.0, 0.0, 8.0), "ground_or_obstacle")
        kind = classify_contact(
            contact,
            obstacle_top_z=0.1,
            obstacle_front_x=1.0,
            top_tolerance_m=0.01,
            riser_tolerance_m=0.01,
            min_upward_force_n=1.0,
        )
        self.assertEqual(kind, ContactClass.STEP_RISER)
        self.assertFalse(is_valid_support(kind, 8.0, 1.0))


if __name__ == "__main__":
    unittest.main()
