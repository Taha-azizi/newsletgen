#%%import os

from dotenv import load_dotenv

load_dotenv() 

#%%
import ollama
response = ollama.web_search("What is Ollama?")
print(response)

#%%
from ollama import web_fetch

result = web_fetch('https://www.linkedin.com/in/taha-azizi-43ba7619/')
print(result)


# %%
