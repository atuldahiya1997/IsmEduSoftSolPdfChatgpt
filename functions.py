
import json
import uuid
from sklearn.metrics.pairwise import cosine_similarity
import time
import numpy as np
import openai
from openai.embeddings_utils import get_embedding, cosine_similarity
import PyPDF2


def learn_pdf(file_path):
    content_chunks = []
    pdf_file = open(file_path, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page in pdf_reader.pages:
        content = page.extract_text()
        obj = {
            "id": str(uuid.uuid4()),
            "text": content,
            "embedding": get_embedding(content, engine='text-embedding-ada-002')
        }
        content_chunks.append(obj)
    ## Save the learned data into the knowledge base...
    json_file_path = 'my_knowledgebase.json'
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for i in content_chunks:
        data.append(i)
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    pdf_file.close()


def Answer_from_documents(user_query):
    user_query_vector = get_embedding(user_query, engine='text-embedding-ada-002')
    with open('my_knowledgebase.json', 'r', encoding="utf-8") as jsonfile:
        data = json.load(jsonfile)
        for item in data:
            item['embeddings'] = np.array(item['embedding'])

        for item in data:
            item['similarities'] = cosine_similarity(item['embedding'], user_query_vector)
        sorted_data = sorted(data, key=lambda x: x['similarities'], reverse=True)

        context = ''
        for item in sorted_data[:2]:
            context += item['text']

        myMessages = [
            {"role": "system", "content": "You're a helpful Assistant."},
            {"role": "user",
             "content": "The following is a Context:\n{}\n\n Answer the following user query according to the above "
                        "given context.\n\nquery: {}".format(
                 context, user_query)}
        ]

        max_retries = 3
        retry_delay = 5  # seconds
        retries = 0
        while retries < max_retries:
            try:
                response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=myMessages,
                    max_tokens=200
                )
                return response['choices'][0]['message']['content']
            except openai.error.ServiceUnavailableError:
                print("Server is overloaded. Retrying after a delay...")
                time.sleep(retry_delay)
                retries += 1



def save_uploaded_file(uploaded_file):
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())