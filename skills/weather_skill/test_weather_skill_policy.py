import unittest
import json
from weather_skill import WeatherSkill


class TestWeatherSKillPolicy(unittest.TestCase):
    def setUp(self):
        self.ws = WeatherSkill()

    def test_basic_case(self):
        """
        Test case when input data has weather intent detected
        and city specification
        :return:
        """
        with open("data/sample_input_with_city.json") as fil:
            json_data = json.load(fil)

        # print(json_data)

        dialogs = json_data
        responses, confidences, _, _, _ = self.ws(dialogs)
        # print(responses[0])
        # works for dummy weather service:
        # self.assertEqual(responses[0], 'Weather in boston is good. 5 above zero')
        # works for openweather map:
        self.assertIn('It is', responses[0])

    def test_missed_location_case(self):
        """
        Test case when input data has weather intent but no city specification
        :return:
        """
        with open("data/sample_input_without_city.json") as fil:
            json_data = json.load(fil)

        # print(json_data)

        dialogs = json_data
        # print(self.ws(dialogs))
        responses, confidences, _, _, _ = self.ws(dialogs)
        self.assertEqual(responses[0], 'Hmm. Which particular city would you like a weather forecast for?')

    def test_response_to_location_question_with_next_forecast(self):
        """Test case when user answers with city entity after question about
        the city"""

        with open("data/sample_input_after_city_question.json") as fil:
            json_data = json.load(fil)

        # print(json_data)

        dialogs = json_data
        responses, confidences, _, _, _ = self.ws(dialogs)
        # works for dummy weather service:
        # self.assertEqual('Weather in boston is good. 5 above zero', responses[0])

        # works for openweather map:
        self.assertIn('It is', responses[0])

    def test_response_to_location_question_with_ignorance_and_forgetting(self):
        """Test case when question asked by answer contains no entity"""

        with open("data/sample_input_forget_case.json") as fil:
            json_data = json.load(fil)

        # print(json_data)

        dialogs = json_data
        responses, confidences, _, _, _ = self.ws(dialogs)
        self.assertIn(responses[0], ['', "Sorry, I have no weather for the place. I didn't recognize the city..."])


if __name__ == '__main__':
    unittest.main()
