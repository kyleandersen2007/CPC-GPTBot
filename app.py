from flask import Flask, render_template, request
from openai import OpenAI
import os
from dotenv import load_dotenv

previous_questions_and_answers = []

load_dotenv()
app = Flask(__name__)

api_key = os.environ.get("OPEN_API_KEY")

@app.route("/")
def index():
    return render_template('index.html')


@app.route("/get", methods=["GET", "POST"])
def chat():
    global previous_questions_and_answers
    msg = request.form["msg"]
    input_text = msg

    if input_text == "test":
        return "This is a test response, fella!"
    else:
        response = get_openai_response(input_text)

        previous_questions_and_answers.append((input_text, response))
        return response
        

def get_openai_response(prompt):
    global previous_questions_and_answers
    client = OpenAI(api_key=api_key)
    MODEL = "gpt-3.5-turbo"

    messages = [
        { "role": "system", "content": "You are First Name Max, last name Spillner, be extremely consise" },
    ]
    for question, answer in previous_questions_and_answers[-100:]:
        messages.append({ "role": "user", "content": question })
        messages.append({ "role": "assistant", "content": answer })
    messages.append({ "role": "user", "content": prompt })

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
        max_tokens=10    
    )

    r = response.choices[0].message.content
    print(response)
    previous_questions_and_answers.append((prompt, r))

    return r

if __name__ == '__main__':
    port = 5050
    app.run('0.0.0.0', port)