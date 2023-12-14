import streamlit as st
import json
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
import os


# Read API key
api_key = st.secrets["api_key"]

# 1. Vectorise the sales response csv data
dir_path = os.path.dirname(os.path.realpath(__file__))
csv_file_path = os.path.join(dir_path, 'training_data.csv')
loader = CSVLoader(file_path=csv_file_path)
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
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k-0613", openai_api_key=api_key)

# need to edit the template
template = """
You are an expert on "The Hunger Games".

Below is a question about the book:
{question}

Based on the knowledge from the book and similar past questions and answers, provide a detailed and accurate answer:
{past_answers}

Here is the best answer to the question:
"""

prompt = PromptTemplate(
    input_variables=["question", "past_answers"],
    template=template
)

chain = LLMChain(llm=llm, prompt=prompt)


# 4. Retrieval augmented generation
def generate_response(question):
    past_answers = retrieve_info(question)
    response = chain.run(question=question, past_answers=past_answers)
    return response


# 5. Build an app with streamlit
def main():
    st.set_page_config(
        page_title="Hunger Games Expert", page_icon=":bird:")

    st.header("Hunger Games Quiz Expert :bird:")

    with st.sidebar:
        st.write("Question Guide")
        st.markdown("""
            - Ask about characters and their relationships
            - Inquire about plot points or themes
            - Explore settings and world-building details
            - Seek explanations for specific events in the story
            """)
        
    # adding in a history section
    if 'query_history' not in st.session_state:
        st.session_state['query_history'] = []

    message = st.text_area("Please type your question on Hunger Games below!")
    if message:
        st.write("Generating response...")

        result = generate_response(message)

        st.info(result)
        # save to history
        st.session_state['query_history'].append(message)

        # Display history
        st.write("Past Questions:")
        for past_query in st.session_state['query_history']:
            st.write(past_query)


if __name__ == '__main__':
    main()
