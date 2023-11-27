# Hunger Games Quiz Expert

## Description
Hunger Games Quiz Expert is a Streamlit application designed to answer questions about "The Hunger Games" series. It uses machine learning models to provide detailed and accurate answers based on the book and similar past questions and answers.

## Features
- Ask detailed questions about characters, plot, themes, and world-building in "The Hunger Games".
- Get AI-generated responses based on a trained model.
- History of past questions for reference.

## How It Works
The application uses a combination of CSV data loading, FAISS for vector storage, OpenAI embeddings for document embedding, and LangChain for prompt engineering and response generation.

## Installation
To run this application, you will need Python installed on your system. 

1. **Clone the Repository**: 
   ```sh
    git clone https://github.com/joellohweien/DataProjects.git
    cd DataProjects/DataScience/HungerGamesExpert/
   ```
2. **Set Up a Virtual Environment**:
  ```sh
  python3 -m venv env
  source env/bin/activate  # On Windows use `env\Scripts\activate`
  ```
3. **Install Dependencies**:
  ```sh
  pip install -r requirements.txt
  ```
4. **API Key Configuration**:
  - Create a config.json file with your OpenAI API key:
  ```sh
  {
    "api_key": "your-openai-api-key"
  }
  ```
5. **Run the Application**:
  ```sh
  streamlit run qna_chatbot_gpt_faiss.py
  ```

## Usage
- Upon launching the application, you will see a text area where you can type in your question about "The Hunger Games"
- After submitting your question, the AI model generates a response based on the trained data
- The sidebar provides guidance on the types of questions you can ask

## Data Training
- The training_data.csv was prepared using book_parse.py
- This script analyzes text from "The Hunger Games" PDF and generates questions and answers using an AI model

## Contributing
- Feedback and contributions to this project are welcome. You can submit issues and pull requests on GitHub
