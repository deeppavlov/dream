# from programy.utils.logging.ylogger import YLogger
from programy.services.service import Service
import datetime as dt
import pytz

# ###########################################################
# CONSTANTS BLOCK
TIMEZONE = "US/Central"
# constants for parts of daytime:
NIGHT_BEGINS_AT = 23
EVENING_BEGINS_AT = 18
DAY_BEGINS_AT = 12
MORNING_BEGINS_AT = 7
# daytime_categories:
MORNING, DAY, EVENING, NIGHT = ("morning", "day", "evening", "night")
# ###########################################################


def classify_current_time(dt_obj=None):
    """
    Given datetime returns a part of day
    :param dt_obj: datetime object or None (then now() is used)
    :return: constant of daytime_category
    """
    if not dt_obj:
        # dt_obj = dt.datetime.now()
        dt_obj = dt.datetime.now(pytz.timezone(TIMEZONE))
        # print(dt_obj)

    if dt_obj.hour >= NIGHT_BEGINS_AT or dt_obj.hour < MORNING_BEGINS_AT:
        # night
        return NIGHT
    elif dt_obj.hour >= EVENING_BEGINS_AT and dt_obj.hour < NIGHT_BEGINS_AT:
        # evening
        return EVENING
    elif dt_obj.hour >= DAY_BEGINS_AT and dt_obj.hour < EVENING_BEGINS_AT:
        # day
        return DAY
    elif dt_obj.hour >= MORNING_BEGINS_AT and dt_obj.hour < DAY_BEGINS_AT:
        # morning
        return MORNING


class DayTimeClfService(Service):
    """
    AIML Service that classifies time into 4 classes:
    - evening,
    - night,
    - morning,
    - day
    and puts it into user_variable `time_of_day`
    """

    def __init__(self, config=None, api=None):
        Service.__init__(self, config)

    def ask_question(self, client_context, question: str):
        time_of_day = classify_current_time()
        # service adds a property with part of date for usage by greeting templates:
        # https://github.com/keiffster/program-y/issues/244
        # doesn't work unexpectedly:
        client_context.brain.properties.add_property("time_of_day", time_of_day)
        # http://192.168.10.188:8081/index.php/ProgramY_Overview#Setting_and_getting_dynamic_variables

        client_context.brain.rdf.add_entity("time_of_day", "is", time_of_day, "timeofday")
        return None
