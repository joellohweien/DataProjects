import PyPDF2
import json
import requests

url = "http://localhost:11434/api/generate"
headers = {
    'Content-Type': 'application/json',
}

command = """Analyze the following text and provide one key question and its answer. Format your response as a single JSON object: {"data":{"Question": "Derived question", "Answer": "Relevant answer"}}. \n"""

def run(user_input):
    data = {
        "model": "zephyr",
        "stream": False,
        "prompt": user_input
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_text = response.json()
        return response_text.get('response')
    else:
        print("Error:", response.status_code, response.text)
        return None

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as pdf_file_obj:
        pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
        text = ''.join(page.extract_text() for page in pdf_reader.pages)
    return text

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def submit_to_api(chunk, retries=3):
    for i in range(retries):
        try:
            response = run(command + chunk.strip())
            print("Raw model response obtained. Attempted to parse JSON...")

            # Check if the response is a string and try to parse it as JSON
            if isinstance(response, str):
                try:
                    response_json = json.loads(response)
                    print("Valid JSON response!")
                    return response_json
                except json.JSONDecodeError as e:
                    print("JSON parsing error:", e)
                    print("Invalid JSON response:", response)

            else:
                print("Unexpected response format:", response)

        except Exception as e:
            print(f"Error during request: {e}")
            continue

    print("Max retries exceeded. Skipping this chunk.")
    return None


def main():
    text = extract_text_from_pdf('thehungergames1.pdf')
    text_chunks = list(chunks(text, 2048))

    for chunk in text_chunks:
        response = submit_to_api(chunk)
        if response is not None:
            with open('responses.json', 'a') as f:
                json.dump(response, f)
                f.write('\n')

if __name__ == "__main__":
    try:
        main()  
    except KeyboardInterrupt:
        print("\nScript interrupted. Partial data saved in 'responses.json'.")
