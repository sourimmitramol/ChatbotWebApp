# application.py
from flask import Flask, request, jsonify
from flasgger import Swagger
from final_chatbot import query_chatbot

app = Flask(__name__)
swagger = Swagger(app)

@app.route("/")
def hello():
    return "<h1>Hello World!</h1>"

@app.route('/ask', methods=['POST'])
def ask():
    """
    Ask the chatbot a question
    ---
    post:
      summary: Ask a logistics-related question
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                question:
                  type: string
                  example: "Where is my container?"
      responses:
        200:
          description: Response from chatbot
          content:
            application/json:
              schema:
                type: object
                properties:
                  response:
                    type: string
        500:
          description: Internal error
    """
    try:
        data = request.get_json()
        question = data.get("question")
        if not question:
            return jsonify({"error": "Missing 'question' field"}), 400
        #answer = query_chatbot(question)
        answer = "test"
        if answer is None:
            return jsonify({"error": "No response from chatbot"}), 500
        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
        
