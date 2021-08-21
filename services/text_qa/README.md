# Fact Retrieval

The service finds the answer of a factoid question in text.

Example of query.

```python
requests.post("http://0.0.0.0:8078/model", json = {"question_raw": ["Who was the founder of Apple?"],
                                                   "top_facts": [["Apple was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976 to develop and sell Wozniak's Apple I personal computer, though Wayne sold his share back to Jobs and Wozniak within 12 days.fix"]]}).json()
```

Output: [['Steve Jobs',
          0.9962880611419678,
          21,
          "Apple was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976 to develop and sell Wozniak's Apple I personal computer, though Wayne sold his share back to Jobs and Wozniak within 12 days."]]
