import re
import json

with open('common/places2visit.json', 'r') as f:
    places2visit = json.load(f)

# recommend me a place to visit
# where should i ... vacation/holiday
# what place should i visit
# recommend me where to go for holiday
# where (i can/can i) vacation
# where to vacation

TRAVEL_RECOMMENDATION_PATTERN = re.compile(r"\b(where.*?(vacation|holiday|travel|weekend)|(recommend|suggest).*?(country|vacation|holiday|travel|weekend|place to (go|visit)))", re.IGNORECASE)
