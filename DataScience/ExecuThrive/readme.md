# ExecuThrive - Executive Coaching & Wellness App

## Description
ExecuThrive is an web-app designed to empower executives by blending traditional executive coaching with insights from classic, yet often less accessible, texts. ExecuThrive offers a distinct perspective by delving into the wisdom of historical and strategic literature, providing modern leaders with an enriched understanding of time-tested principles.

## Features
- In-depth queries about executive leadership, communication skills, and personal challenges
- Tailored responses focusing on professional development and personal well-being
- History tracking of past inquiries for self-reflection and growth

## How It Works
The app leverages advanced AI techniques, including CSV data loading for contextual understanding, FAISS for data retrieval, OpenAI embeddings, and LangChain for prompt crafting and response formulation.

## Installation
Please note that you would need Python installed on your system to run ExecuThrive.

1. **Clone the Repository**: 
   ```sh
   git clone https://github.com/your-username/ExecuThrive.git
   cd ExecuThrive/
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
  streamlit run executhrive.py
  ```
## Usage
- Start the app to access a browser where you can type your executive or personal well-being related questions
- The AI system will analyze your query and provide a thoughtful, comprehensive response
- To start you off, suggested questions are included in the sidebar

## Data Training
ExecuThrive showcases a POC for using Retrieval-Augmented Generation (RAG) to extract and apply wisdom from key historical and strategic texts. 
- "Memoirs of Extraordinary Popular Delusions and the Madness of Crowds" by Charles Mackay, unveiling the intricacies of crowd psychology and market dynamics
- "The Art of Money Getting; Or, Golden Rules for Making Money" by P.T. Barnum, offering sage advice on financial acumen and wealth management
- "Simple Sabotage Field Manual" by the United States Office of Strategic Services, revealing insights into overcoming organizational and personal challenges
- "The Prince" by Niccolò Machiavelli, providing a masterclass in power dynamics and strategic leadership
- "The Merchant of Venice" by William Shakespeare, exploring ethical dilemmas and the human condition
- "The Art of War" by Sun Tzu, articulating timeless strategies applicable in both the battlefield and the boardroom

## Contributing
- Feedback and contributions to this project are welcome. You can submit issues and pull requests on GitHub
