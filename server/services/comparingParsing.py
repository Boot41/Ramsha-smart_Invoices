import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def extract_text(path):
    """Extracts text from a PDF file."""
    with pdfplumber.open(path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text

def preprocess_text(text):
    """Preprocesses text by converting to lowercase, removing special characters, and extra whitespace."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text) # Replace multiple whitespaces with a single space
    text = re.sub(r'[^\w\s]', '', text) # Remove non-alphanumeric characters
    return text.strip()

def compute_cosine_similarity(original_text, parsed_text):
    """Computes the cosine similarity between original and parsed texts."""
    vectorizer = TfidfVectorizer()
    # Input for TfidfVectorizer should be lists of strings
    originalVector = vectorizer.fit_transform([original_text]) # Fit-transform the original text
    parsedVector = vectorizer.transform([parsed_text]) # Transform the parsed text
    similarity = cosine_similarity(originalVector, parsedVector)
    # Since we're comparing two single documents, similarity will be a 1x1 matrix
    return similarity[0][0] # Extract the scalar similarity value

def compare_parsing(path: str, parsed_text: str):
    """
    Compares the original PDF text and parsed text, returning the cosine similarity.
    """
    try:
        # Extract and preprocess the original text
        original_text = extract_text(path)
        original_text_preprocessed = preprocess_text(original_text)

        # Preprocess the parsed text
        parsed_text_preprocessed = preprocess_text(parsed_text)

        # Compute cosine similarity
        overall_similarity = compute_cosine_similarity(original_text_preprocessed, parsed_text_preprocessed)
        return overall_similarity
    except Exception as e:
        raise RuntimeError(f"Error occurred while processing file {path}: {str(e)}")
