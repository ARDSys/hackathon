import glob
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


embedding_model = OpenAIEmbeddings()

persist_directory = "./chroma_books"

if os.path.exists(persist_directory) and os.listdir(persist_directory):
    print("Loading vectorstore from cache...")
    vectorstore = Chroma(
        persist_directory=persist_directory, embedding_function=embedding_model
    )
else:
    pdf_folder = "../books/"
    pdf_paths = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    all_docs = []
    for file_path in pdf_paths:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        print(f"Loaded {len(docs)} pages from {file_path}")
        all_docs.extend(docs)
    print(f"Total loaded documents: {len(all_docs)}")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    print("Creating new vectorstore and caching it...")
    splits = text_splitter.split_documents(all_docs)
    print(f"Split the documents into {len(splits)} chunks.")
    vectorstore = Chroma.from_documents(
        documents=splits, embedding=embedding_model, persist_directory=persist_directory
    )
    vectorstore.persist()

retriever = vectorstore.as_retriever()

llm = ChatOpenAI(model="gpt-4o")

system_prompt = (
    "You are an assistant that provides concise answers based on the provided context. "
    "Use the following retrieved context from the rheumatology book(s) to answer the question. "
    "If the answer is not found in the context, say you don't know. "
    "Limit the answer to three sentences.\n\nContext:\n{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("human", "{input}")]
)

# RAG
question_answer_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)
query = "What is the definition of rheumatoid arthritis mentioned in the book?"
results = rag_chain.invoke({"input": query})

print("\nAnswer:", results.get("answer", "No answer found."))
