import unittest
from pathlib import Path

from applier.htmlform import questions_from_html
from applier.models import FormField, FormQuestion, Option, Profile
from applier.practice import practice_profile, render_apply, success_questions
from applier.questions import plan_application


def profile(**overrides) -> Profile:
    base = practice_profile(Path("resume.pdf"))
    data = base.__dict__.copy()
    data.update(overrides)
    return Profile(**data)


def question(label, required=True, kind="text", name="q", options=()):
    return FormQuestion(label, required, (FormField(name, kind, tuple(options)),))


class PlanTests(unittest.TestCase):
    def test_practice_form_is_fully_answered(self):
        plan = plan_application(success_questions(), profile(), "Hello there")
        self.assertTrue(plan.ok, plan.reason)
        values = {answer.name: answer.value for answer in plan.answers}
        self.assertEqual(values["work_auth"], "Yes")
        self.assertEqual(values["sponsorship"], "No")
        self.assertEqual(values["salary"], "80000")
        self.assertEqual(values["school"], "Example State University")
        self.assertEqual(values["veteran_status"], "I don't wish to answer")
        self.assertEqual(values["first_name"], "Practice")
        self.assertNotIn("snack", values)
        self.assertNotIn("favorite_color", values)

    def test_unknown_required_question_skips(self):
        questions = success_questions() + (
            question("What is your favorite color?", kind="select", name="favorite_color", options=(Option("Red", "Red"), Option("Blue", "Blue"))),
        )
        plan = plan_application(questions, profile(), "Hello")
        self.assertFalse(plan.ok)
        self.assertIn("favorite color", plan.reason.lower())

    def test_sponsorship_yes_does_not_pick_a_visa(self):
        questions = (
            question(
                "Will you now or in the future require sponsorship for a visa?",
                kind="select",
                name="sponsorship",
                options=(
                    Option("0", "No"),
                    Option("1", "Yes, Netherlands Highly Skilled Migrant Visa"),
                ),
            ),
        )
        plan = plan_application(questions, profile(needs_sponsorship="yes"), "")
        self.assertFalse(plan.ok)

    def test_empty_extra_answer_does_not_invent_aws(self):
        questions = (question("Which AWS certification do you hold?", name="aws"),)
        plan = plan_application(questions, profile(), "")
        self.assertFalse(plan.ok)
        filled = plan_application(questions, profile(extra_answers=(profile().extra_answers[0],) + tuple()), "")
        # The practice extras include a blank aws phrase. A real answer is required.
        self.assertFalse(filled.ok)

    def test_aws_answer_does_not_match_laws(self):
        from applier.models import ExtraAnswer

        person = profile(extra_answers=(ExtraAnswer("aws", "AWS Cloud Practitioner"),))
        laws = plan_application((question("Do you follow the laws?", name="laws"),), person, "")
        self.assertFalse(laws.ok)
        cert = plan_application((question("Which AWS certification do you hold?", name="aws"),), person, "")
        self.assertTrue(cert.ok)
        self.assertEqual(cert.answers[0].value, "AWS Cloud Practitioner")

    def test_required_gender_without_decline_option_is_skipped(self):
        questions = (
            question(
                "Gender",
                kind="select",
                name="gender",
                options=(Option("1", "Woman"), Option("2", "Man")),
            ),
        )
        plan = plan_application(questions, profile(gender="decline"), "")
        self.assertFalse(plan.ok)

    def test_optional_unknown_is_left_blank(self):
        questions = success_questions()[:3] + (question("Favorite snack", required=False, name="snack"),)
        plan = plan_application(questions, profile(), "")
        self.assertTrue(plan.ok)
        self.assertNotIn("snack", {answer.name for answer in plan.answers})

    def test_hidden_coordinates_are_not_invented(self):
        questions = (
            question("Location", name="location"),
            FormQuestion("Latitude", True, (FormField("latitude", "hidden"),)),
            FormQuestion("Longitude", True, (FormField("longitude", "hidden"),)),
        )
        plan = plan_application(questions, profile(city="Raleigh"), "")
        self.assertTrue(plan.ok, plan.reason)
        self.assertEqual([answer.name for answer in plan.answers], ["location"])

    def test_country_alias_and_reside_question(self):
        country = question(
            "What is your current country of residence?",
            kind="select",
            name="country",
            options=(Option("1", "Canada"), Option("2", "United States"), Option("3", "Germany")),
        )
        reside = question(
            "Do you reside in the United States or Canada?",
            kind="select",
            name="reside",
            options=(Option("1", "Yes"), Option("0", "No")),
        )
        plan = plan_application((country, reside), profile(country="US"), "")
        self.assertTrue(plan.ok, plan.reason)
        values = {answer.name: answer.value for answer in plan.answers}
        self.assertEqual(values["country"], "United States")
        self.assertEqual(values["reside"], "Yes")
        germany = plan_application((reside,), profile(country="Germany"), "")
        self.assertEqual(germany.answers[0].value, "No")

    def test_html_form_round_trip(self):
        parsed = questions_from_html(render_apply("se-remote"))
        plan = plan_application(parsed, profile(), "Hello there")
        self.assertTrue(plan.ok, plan.reason)
        self.assertEqual({answer.name: answer.value for answer in plan.answers}["sponsorship"], "No")


if __name__ == "__main__":
    unittest.main()
