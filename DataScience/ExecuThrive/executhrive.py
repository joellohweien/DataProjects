import streamlit as st
import json
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain


# Read API key
try:
    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)
        api_key = config_data["api_key"]
except FileNotFoundError:
    st.error("Config file not found.")
    exit()
except KeyError:
    st.error("API key not found in config file.")
    exit()

# 1. Vectorise the sales response csv data
loader = CSVLoader(file_path="./managementcoach/books_qna.csv")
documents = loader.load()
embeddings = OpenAIEmbeddings(openai_api_key=api_key)
db = FAISS.from_documents(documents, embeddings)

# 2. Function for similarity search

def retrieve_info(query):
    similar_response = db.similarity_search(query, k=3)

    page_contents_array = [doc.page_content for doc in similar_response]

    # print(page_contents_array)

    return page_contents_array


# 3. Setup LLMChain & prompts
llm = ChatOpenAI(temperature=0.9, model="gpt-4-1106-preview", openai_api_key=api_key) #gpt-3.5-turbo-16k-0613

# need to edit the template
# Revised Prompt Template
template = """
As an executive management coach utilizing advanced AI tools, you are tasked to answer the following business-related question: {question}

Your response should be informed by a blend of your extensive knowledge in business literature and the insights drawn from similar past queries. For each step in crafting your response, consider the following guidelines:

1/ Utilize the insights derived from similar past queries provided by the AI-driven similarity search. Reflect on these insights to ensure your response is well-informed and contextually relevant from {past_answers}.

2/ If the current query extends beyond the scope of these past insights, expand your response using general business principles and theories. Clearly indicate which parts of your response are based on these broader principles.

3/ Continuously evaluate if additional searches are needed to enhance the quality of your response. If so, integrate new findings seamlessly into your existing knowledge base.

4/ Ensure that your response is factual and data-driven, drawing upon the specific examples or teachings from past insights and general business knowledge.

5/ In cases where new searches have been conducted, include a brief summary of these additional insights, demonstrating how they contribute to the comprehensiveness of your response.

6/ In your final output, you should summarise the response, and NOT mention that there was a search history.

Here is your well-researched, comprehensive, and contextually relevant answer to the question:
"""

prompt = PromptTemplate(
    input_variables=["question", "past_answers"],
    template=template
)

chain = LLMChain(llm=llm, prompt=prompt)


# 4. Retrieval augmented generation
def generate_response(question):
    past_answers = retrieve_info(question)
    response = chain.run(
        question=question, 
        past_answers=past_answers
        )
    return response



# 5. Build an app with streamlit

def main():
    st.set_page_config(
        page_title="Executive Coach", page_icon=":anchor:")

    st.header("Executive Coach :anchor:")

    with st.sidebar:
        st.write("Question Guide")
        st.markdown("""
            - **Communication Skills**: *"How can effective communication skills in executive leadership help in managing personal stress and maintaining work-life balance?"*
            - **Innovation and Change**: *"In fostering a culture of innovation and managing organizational change, how can I also adapt to personal life changes and challenges?"*
            - **Organizational Culture**: *"How can aligning my personal values with the organizational culture influence and shape a more empathetic and understanding workplace?"*
            - **Leadership Challenges**: *"What strategies can help in overcoming leadership challenges while dealing with personal pressures, such as financial stress or maintaining relationships?"*
            """)
        
    # adding in a history section
    if 'query_history' not in st.session_state:
        st.session_state['query_history'] = []

    message = st.text_area("Please type your question here!")

    # Create a placeholder
    status_message = st.empty()

    if message:
        # Update the placeholder with the generating response message
        status_message.write("Generating response...")

        result = generate_response(message)

        # Once the response is generated, update the message
        status_message.write("Response Generated!")

        st.info(result)
        # save to history
        st.session_state['query_history'].append(message)

        # Display history
        st.write("Past Questions:")
        for past_query in st.session_state['query_history']:
            st.write(past_query)

if __name__ == "__main__":
    main()
