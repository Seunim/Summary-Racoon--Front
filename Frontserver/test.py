import requests
import json

input_data = {
    "text": "i have a dog with a beautiful smile",
    "summary": "i have a dog"
}

print(type(input_data))
response = requests.get("https://asdasdinfer.run.goorm.site/testsummary", json=json.dumps(input_data))

print(response)
