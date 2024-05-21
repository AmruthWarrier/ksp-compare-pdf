from flask import Flask, request, jsonify
import os
import PyPDF2
from gensim import corpora, similarities, models
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS

app = Flask(__name__)

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

# Function to preprocess text data
def preprocess_text(text):
    text = text.lower()
    text = ''.join([char for char in text if char.isalnum() or char.isspace()])
    tokens = simple_preprocess(text)
    tokens = [token for token in tokens if token not in STOPWORDS]
    return tokens

# Function to compute similarity between two texts
def compute_similarity(input_text, stored_text):
    dictionary = corpora.Dictionary([stored_text])
    corpus = [dictionary.doc2bow(input_text)]
    tfidf = models.TfidfModel(corpus)
    index = similarities.SparseMatrixSimilarity(tfidf[corpus], num_features=len(dictionary))
    sims = index[tfidf[dictionary.doc2bow(stored_text)]]
    return sims[0]

# Function to find the most similar PDF among stored PDFs
def find_most_similar(input_pdf_path, stored_pdf_folder):
    input_text = preprocess_text(extract_text_from_pdf(input_pdf_path))
    most_similar_pdf = None
    highest_similarity = -1

    for filename in os.listdir(stored_pdf_folder):
        if filename.endswith(".pdf"):
            stored_pdf_path = os.path.join(stored_pdf_folder, filename)
            stored_text = preprocess_text(extract_text_from_pdf(stored_pdf_path))
            similarity = compute_similarity(input_text, stored_text)
            if similarity > highest_similarity:
                highest_similarity = similarity
                most_similar_pdf = stored_pdf_path

    return most_similar_pdf

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "hello"}), 200

@app.route('/compare_pdfs', methods=['POST'])
def compare_pdfs():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    input_pdf_path = "/tmp/input_pdf.pdf"
    file.save(input_pdf_path)

    stored_pdf_folder = "stored_pdfs"

    most_similar_pdf = find_most_similar(input_pdf_path, stored_pdf_folder)
    if most_similar_pdf:
        return jsonify({"most_similar_pdf": most_similar_pdf}), 200
    else:
        return jsonify({"error": "No similar PDF found"}), 404

if _name_ == '_main_':
    app.run(debug=True)