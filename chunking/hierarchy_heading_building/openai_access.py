import openai
import time
import logging
import requests

logger = logging.getLogger(__name__)

def get_oai_completion(prompt, api_base, api_key, api_type, api_version, engine, temperature = 0, top_p = 0.7, max_tokens = 2048, stream = False):
    openai.api_key = api_key
    openai.api_type = api_type
    openai.api_base = api_base
    openai.api_version = api_version

    try: 
        response = openai.ChatCompletion.create(
#   model="gpt-3.5-turbo",
#   engine='gpt35',
  engine=engine,
  messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
       
    ],
   temperature=temperature,
   max_tokens=max_tokens,
   top_p=top_p,
   frequency_penalty=0,
   presence_penalty=0,
   stop=None,
   stream=stream
)
        if not stream:
            res = response["choices"][0]["message"]["content"]
            gpt_output = res
            return gpt_output
        else:
            def convert_to_content(chunk):
                if len(chunk["choices"]) > 0:
                    return chunk.choices[0].delta.get("content", "")
                return ""
            return (
                convert_to_content(chunk)
                for chunk in response
            )
    except requests.exceptions.Timeout:
        # Handle the timeout error here
        print("The OpenAI API request timed out. Please try again later.")
        return None
    except openai.error.InvalidRequestError as e:
        # Handle the invalid request error here
        print(f"The OpenAI API request was invalid: {e}")
        return None
    except openai.error.APIError as e:
        if "The operation was timeout" in str(e):
            # Handle the timeout error here
            print("The OpenAI API request timed out. Please try again later.")
#             time.sleep(3)
            return get_oai_completion(prompt)            
        else:
            # Handle other API errors here
            print(f"The OpenAI API returned an error: {e}")
            return None
    except openai.error.RateLimitError as e:
        return get_oai_completion(prompt)

def call_chatgpt(ins, api_base, api_key, api_type, api_version, engine, temperature, top_p, max_tokens, stream = False):
    success = False
    re_try_count = 15
    ans = ''
    while not success and re_try_count >= 0:
        re_try_count -= 1
        try:
            ans = get_oai_completion(ins, api_base, api_key, api_type, api_version, engine, temperature, top_p, max_tokens, stream)
            success = True
        except Exception as e:
            logging.error("Error when calling gpt: %s", e)
            time.sleep(5)
            logging.info('Retry count left: %d', re_try_count)
    return ans