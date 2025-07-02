import pandas as pd
from docx import Document
import pdfplumber
import openai,pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from PIL import Image
import pytesseract
import os
import ast
import requests
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PINECONE_API_KEY
from pyairtable import Table

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
def extract_text_from_excel(path):
    try:
        df = pd.read_excel(path)
        # Concatenate all cell values as strings
        text = ""
        for col in df.columns:
            text += " ".join(df[col].astype(str).tolist()) + "\n"
        return text
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return ""

def extract_text_from_docx(path):
    try:
        doc = Document(path)
        return "\n".join([para.text for para in doc.paragraphs if para.text])
    except Exception as e:
        print(f"Error reading Word: {e}")
        return ""

def extract_text_from_pdf(path):
    try:
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def extract_text_from_image(path):
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error reading image: {e}")
        return ""


FILE_HANDLERS = {
".xlsx": extract_text_from_excel,
".xls": extract_text_from_excel,
".docx": extract_text_from_docx,
".doc": extract_text_from_docx,
".pdf": extract_text_from_pdf,
}


def download_file_from_drive(drive_url: str, output_path: str, chunk_size=32768):
    """Downloads a file from a direct Drive URL to a local file path."""
    response = requests.get(drive_url, stream=True)
    response.raise_for_status()  # Will raise HTTPError if failed
    print(f"Opening file for writing: {output_path}")
    with open(output_path, "wb") as file:
        print(f"Downloading file in chunks of size {chunk_size} bytes...")
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                file.write(chunk)
    print(output_path)
    return output_path

def process_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in FILE_HANDLERS:
        raise ValueError(f"Unsupported file type: {ext}")
    handler_function = FILE_HANDLERS[ext]
    return handler_function(filepath)


def process_documents(files,client_id):
    try:
        text= ""
        for file in files:
            text+= process_file(file) + "\n"

        print(f"Creating Pinecone index and embedding the document...")
        
        pc = Pinecone(
            api_key=PINECONE_API_KEY
        )

        # Now do stuff
        if 'influencer-marketing-brief' not in pc.list_indexes().names():
            pc.create_index(
                name='influencer-marketing-brief', 
                dimension=1536, 
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        index = pc.Index("influencer-marketing-brief")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 200,
        )

        chunks = splitter.split_text(text)

        for i,chunk in enumerate(chunks):
            print(f"Chunk {i+1}: {chunk[:100]}...")  # Print first 100 characters of each chunk
            response = openai_client.embeddings.create(
                input = [chunk],
                model = "text-embedding-ada-002"
            )
            vec = response.data[0].embedding
            meta = {"text": chunk,"client_id":client_id}
            index.upsert(vectors=[(f"{client_id}_{i+1}", vec, meta)])  # Using chunk index as ID

        print("Document indexed successfully.")
        return index
    
    except Exception as e:
        print(f"Error processing documents: {e}")
        return False


# --- Generate filter formula from user query ---
def generate_airtable_formula(query_context,airtable_fields):

    prompt = f"""
        You are an assistant that generates Airtable filterByFormula expressions based on the influencer criteria required by a brand to query relevant influencers.

        Airtable Table Schema:
        {airtable_fields}

        Influencer Criteria required for the brand to query relevant influencers:
        "{query_context}"

        Return only the Airtable formula, with no explanation or markdown.
    """

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    formula = response.choices[0].message.content.strip()
    # Remove code block formatting if present
    if formula.startswith("```"):
        formula = formula.split("```")[1].strip()
    return formula

def airtable_formula_generator(index, client_id, airtable_fields):
    """
    Query Airtable with the given filter formula and return the records.
    """
    try:
        # Embed query and retrieve context
        user_query = """ Create a vector database query to retrieve embedding for this criteria:
                        
                        Find the Ideal Influencer criteria in the influencer brief.
                        Looking for these details:
                        1. Target Audience
                        2. Influencer Followers Count
                        3. Influencer Nationality
                        4. Influencer Region
                        5. Targeted Domain
        """

        q_res = openai_client.embeddings.create(input=[user_query], model="text-embedding-ada-002")
        q_vec = q_res.data[0].embedding

        query_resp = index.query(
            vector=q_vec,
            top_k=5,
            filter={"client_id":client_id},  # restrict to this client's criteria
            include_metadata=True
        )

        retrieved_texts = [match['metadata']['text'] for match in query_resp['matches']]
        print(f"Retrieved {len(retrieved_texts)} relevant chunks for the query.")
        
        query_context = " ".join(retrieved_texts)
        # Step 3: Generate formula
        formula = generate_airtable_formula(query_context,airtable_fields)
        print(f"\n🧠 Generated Formula:\n{formula}\n")
        return formula
    except Exception as e:
        print(f"Error generating formula: {e}")
        return []

def influencer_brief_processing(drive_urls_str, client_id,airtable_fields):
    """
    Process the influencer brief documents and generate SQL query.
    :param files: List of file paths to process.
    :param client_id: Client ID for which the documents are processed.
    :return: SQL query string or None if processing fails.
    """
    drive_urls = ast.literal_eval(drive_urls_str)  # Converts JSON string → Python list
    files = []
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"SCRIPT_DIR: {SCRIPT_DIR}")
    for i,drive_url in enumerate(drive_urls):
        folder_path = f"drive_uploads/demo_{i+1}.docx"
        output_path = os.path.join(SCRIPT_DIR, folder_path)
        print(f"full path: {output_path}")
        files.append(download_file_from_drive(drive_url, output_path))
        print(f"Downloaded file {i+1}: {files[-1]}")
    print(f"Total files downloaded: {len(files)}")
    print(files)
    index = process_documents(files, client_id)
    if index:
        # sql_query = generate_sql_from_influencer_brief(index, client_id)
        formula = airtable_formula_generator(index, client_id, airtable_fields)
        if formula:
            print("Airtable Formula generated successfully.")
            print(formula)
        else:
            print("Failed to generate Airtable Formula.")
    else:
        print("Failed to process documents.")
    return formula

# if __name__ == "__main__":
#     # Example usage
#     drive_urls_str = """["https://drive.google.com/uc?id=1IoCxHQP8dKBgrGLjeUcDq75Y9Ip97dVf&export=download"]"""
#     client_id = "aarka"
#     sql_query = influencer_brief_processing(drive_urls_str, client_id)
    
  