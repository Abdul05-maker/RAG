
# import streamlit as st
# import faiss
# import numpy as np
# import torch
# from transformers import DistilBertTokenizerFast, DistilBertModel
# from PyPDF2 import PdfReader
# import google.generativeai as genai
# import os


# Initialize the Google Generative AI model (Gemini)
# Retrieve the API key from Streamlit secrets

genai.configure(api_key=GOOGLE_API_KEY)
generative_model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize the tokenizer and model
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
model = DistilBertModel.from_pretrained("distilbert-base-uncased")

# Streamlit UI
st.title("AI Chatbot with PDF and RAG")

# PDF Upload
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

# Process the PDF and create FAISS index
index = None
text_data = []

# Process the PDF and create FAISS index
if uploaded_file is not None:
    pdf_reader = PdfReader(uploaded_file)
    text_data = []
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            text_data.append(text)

    if len(text_data) > 0:
        # Convert the text data into embeddings
        embeddings = []
        for text in text_data:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            outputs = model(**inputs)
            embeddings.append(outputs.last_hidden_state.mean(dim=1).detach().cpu().numpy())
        embeddings = np.vstack(embeddings)

        # Create and populate FAISS index
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)

        st.write("PDF processed and indexed. You can now ask questions based on this content.")
    else:
        st.write("No text could be extracted from the uploaded PDF.")

def retrieve_and_generate(query, index, text_data):
    # Generate embeddings for the query
    query_inputs = tokenizer(query, return_tensors="pt")
    query_embedding = model(**query_inputs).last_hidden_state.mean(dim=1).cpu().numpy()

    # Ensure the index is available before searching
    if index is None:
        return "Index has not been created. Please upload a PDF file first."

    # Search the FAISS index for the closest match
    _, indices = index.search(query_embedding, k=1)

    # Handle case where no indices are found
    if indices.shape[0] == 0 or indices[0].size == 0:
        return "No relevant content found."

    relevant_text = text_data[indices[0][0]]

    # Combine the query with the relevant document
    combined_input = f"{relevant_text} {query}"

    # Query the Gemini model
    response = generative_model.generate_content(combined_input)

    return response.text

# Get user input and generate a response
if uploaded_file is not None and index is not None:
    user_input = st.text_input("what is electrcial engineerng:")
    if user_input:
        output = retrieve_and_generate(user_input, index, text_data)
        st.write("Response:")
        st.write(output)
