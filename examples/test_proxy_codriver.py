import os
import urllib.parse
from openai import AzureOpenAI, DefaultHttpxClient
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

# Proxy settings
proxy_url = os.getenv("PROXY_URL")
proxy_username = os.getenv("PROXY_USERNAME")
proxy_password = os.getenv("PROXY_PASSWORD")

# URL encode the username and password
encoded_username = urllib.parse.quote(proxy_username or '')
encoded_password = urllib.parse.quote(proxy_password or '')

proxy_with_auth = f"http://{encoded_username}:{encoded_password}@{proxy_url}"

#print(proxy_with_auth)

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    http_client=DefaultHttpxClient(
        proxies=proxy_with_auth
    )
)

deployment_name = 'gpt-4o'

print('Sending a test completion job')
start_phrase = '''
Tell me a joke about our it department.
'''

response = client.chat.completions.create(
    model=deployment_name,
    frequency_penalty=2.0,
    max_tokens=1000,
    messages=[{"role": "user", "content": start_phrase}],
    presence_penalty=2.0
)

print(response.choices[0].message.content)
