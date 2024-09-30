import json
import re

from flask import Flask
from flask_cors import CORS
import ast
from langchain_google_genai import ChatGoogleGenerativeAI

app = Flask(__name__)
CORS(app)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.0-pro",
    temperature=0,
    max_tokens=4000,
    timeout=None
)

template = """
    {
        "title": ,
        "completed": false
    }
"""

db_init = json.load(open('db.json', 'r'))
print('INITIAL DB STATE')
print(db_init['state'])


def dict_to_json(d):
    return d.__dict__


@app.route('/<api_call>')
def api(api_call):
    db = json.load(open('db.json', 'r'))
    print("INPUT DB STATE")
    print(db['state'])

    llm_input = f"""
        {db["prompt"]}
        API Call (indexes are zero-indexed):
        {api_call}
        
        Database State:
        {db["state"]}
        
        Output the API response as json prefixed with '!API Response!:'. 
        Then output the new database state as json, prefixed with '!New Database State!:'. 
        If the API call is only requesting data, then don't change the database state, 
        but base your 'API Response' off what's in the database.
        Avoid using [] in output. Use proper json format.
        Use double quotes for property and keys.
        Add activity with the following format:
        {template}
        key: title and completed only.
        If all activity deleted, don't delete todos.
    """

    completion = llm.invoke(llm_input).content
    print(completion)

    api_response_match = re.search(r"(?<=!API Response!:)(.*?)(?=!New Database State!:)", completion, re.DOTALL)
    new_database_match = re.search(r"(?<=!New Database State!:)(.*)", completion, re.DOTALL)

    # Extract and clean the text directly from the match groups
    api_response_text = api_response_match.group(1).strip()
    new_database_text = new_database_match.group(1).strip()

    try:
        api_response = json.loads(api_response_text)
    except json.JSONDecodeError:
        api_response = json.loads(new_database_text)

    new_database = json.loads(new_database_text)

    # Print for debugging purposes
    print("API RESPONSE")
    print(api_response)

    print("NEW DATABASE STATE")
    print(new_database)

    # Update database state and save it back to db.json
    db['state'] = new_database
    with open('db.json', 'w') as f:
        json.dump(db, f, indent=4, default=dict_to_json)

    return new_database


if __name__ == '__main__':
    app.run()
