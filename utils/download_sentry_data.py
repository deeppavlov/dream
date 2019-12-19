"""Download sentry data.
usage:
python download_sentry_data.py <org>/<project> <api_key>

example: python utils/download_sentry_data.py \
         dream-university-team/dream-bot-prod 0f445a7a01cb4f31b5a0a0888f86d3765ffb10d3d3824c9daed44e9c21623535
"""
import requests
import sys
import json


if __name__ == '__main__':
    url = 'https://sentry.io/api/0/projects/{0}/events/'.format(sys.argv[1])
    asr_data = []
    try:
        while True:
            response = requests.get(
                url,
                headers={'Authorization': 'Bearer {TOKEN}'.format(TOKEN=sys.argv[2])},
                params={'full': 1}
            )
            data = response.json()
            for event in data:
                event_dict = dict(event)
                if 'ASR top_1' in event_dict['title']:
                    asr_data.append({
                        'title': event_dict['title'],
                        'mean_proba': event_dict['context']['mean_proba'],
                        'token_with_probs': event_dict['context']['token_with_probs']
                    })
            link = response.headers.get('Link')
            if link and '"next"' in link:
                print(f"Getting next page... Current data count: {len(asr_data)}")
                with open('asr_data.json', 'w') as f:
                    json.dump(asr_data, fp=f, ensure_ascii=False)
                url = link.split()[4][1:-2]
            else:
                break
    finally:
        with open('asr_data.json', 'w') as f:
            json.dump(asr_data, fp=f, ensure_ascii=False)
