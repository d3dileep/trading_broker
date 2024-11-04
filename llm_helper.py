import pandas as pd
import google.generativeai as genai
import datetime
import nltk
#nltk.download('punkt')
#nltk.download('punkt_tab')
def llm_helper(template):
    genai.configure(api_key= 'AIzaSyCpEkFX1-Pxz4JRdZdqsF83VT55JIj75qg')
    model = genai.GenerativeModel("gemini-1.5-flash")
    #template = f"""Tell me a joke"""
    response = model.generate_content(template)
    #print(response)
    #print(response["response"])
    #final_response = response["candidates"][0]["content"]["parts"][0]["text"]
    #print(final_response)
    return response

