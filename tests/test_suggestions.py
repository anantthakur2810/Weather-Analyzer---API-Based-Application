import unittest

from weather_analyzer.suggestions import suggest_city_names


class SuggestCityNamesTests(unittest.TestCase):
    def test_returns_fuzzy_match_for_misspelled_city(self) -> None:
        suggestions = suggest_city_names("Mumbay")
        self.assertIn("Mumbai", suggestions)

    def test_history_candidates_are_prioritized(self) -> None:
        suggestions = suggest_city_names("Ponn", history_candidates=["Pune"])
        self.assertEqual(suggestions[0], "Pune")


if __name__ == "__main__":
    unittest.main()
