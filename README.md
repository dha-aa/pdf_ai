
# 📘 PDF Extractor to CSV (AI-powered)

This project automates the conversion of medical exam PDF papers into structured **CSV files** using **PyMuPDF, Tesseract OCR, and OpenAI GPT**.

The workflow:

1. **Extract text** (with OCR support for scanned PDFs) → `txt_outputs/`
2. **Convert text to CSV** (questions, marks, year, paper title, etc.) → `csv_outputs/`
3. **Save results** as both per-exam CSVs and one combined `all_exams_combined.csv`.

---

## 🚀 Features

* Extracts text from PDFs **page by page**
* OCR fallback for scanned PDFs/images
* AI-powered **question-to-CSV conversion**
* Parallel processing for speed (with rate-limit safety)
* Outputs:

  * Per-page `.txt` files
  * Per-exam `.csv` files
  * One combined CSV (`all_exams_combined.csv`)

---

## 📂 Project Structure

```
project/
│── pdfs/              # Place your exam PDFs here
│── txt_outputs/        # Extracted text (auto-created)
│── csv_outputs/        # Final CSV outputs (auto-created)
│── pdf_reader.py       # Extracts text from PDFs
│── ai.py               # Converts text into structured CSV
│── main.py             # Orchestrates full workflow
│── .env                # Stores OpenAI API key
│── README.md           # This file
```

---

## 🛠️ Installation

### 1. Clone project

```bash
git clone git@github.com:dha-aa/pdf_ai.git
cd pdf_ai
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install system dependencies

* **Tesseract OCR** (required for image-based PDFs)

  * Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)
  * macOS: `brew install tesseract`
  * Ubuntu: `sudo apt install tesseract-ocr`

---

## 🔑 Environment Setup

Create a file `.env` in the root project folder with your OpenAI API key:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

⚠️ Never commit `.env` to GitHub.

---

## 📥 Usage

### Step 1: Place PDFs

```
mkdir pdfs
```
Put all your exam PDFs inside the **`pdfs/`** folder.

Example:

```
pdfs/
│── 229000KC (1).pdf
│── 229000KD (2).pdf
```

### Step 2: Run pipeline

Simply run:

```bash
python main.py
```

This will:

1. Extract text → `txt_outputs/`
2. Convert text to CSV → `csv_outputs/`

---

## 📊 Example Output

### Example TXT (`229000KC (1)_page_1.txt`)

```
MARCH 1990
M.S. DEGREE EXAMINATION, MARCH 1990.
Branch I — General Surgery
Part I
APPLIED BASIC SCIENCES
1. Describe the surgical anatomy of the thyroid gland.
2. Write notes on: (a) Deep palmar spaces. (b) Femoral canal.
```

### Example CSV (`229000KC (1).csv`)

```csv
question,marks,paper_title,filename,page,year
"Describe the surgical anatomy of the thyroid gland",5,"M.S. Degree Examination, March 1990 – General Surgery","229000KC (1).pdf",1,1990
"Write notes on: Deep palmar spaces",5,"M.S. Degree Examination, March 1990 – General Surgery","229000KC (1).pdf",1,1990
"Write notes on: Femoral canal",5,"M.S. Degree Examination, March 1990 – General Surgery","229000KC (1).pdf",1,1990
```

### Combined CSV (`all_exams_combined.csv`)

Contains all exams merged together.

---

## ⚡ Troubleshooting

* **Empty text files** → Your PDF is scanned; ensure **Tesseract OCR** is installed.
* **API errors / rate limits** → Reduce thread count (`max_workers`) in `ai.py`.
* **Wrong paper titles/years** → Ensure exam headers are clearly formatted in the PDF.

---

## 📌 Requirements.txt Example

Here’s a sample `requirements.txt` for your project:

```
pymupdf
pytesseract
pillow
python-dotenv
openai
tqdm
```

---

✅ That’s it! Place PDFs → Run `main.py` → Get clean CSV exam datasets.

---
▶️ [Watch the demo on YouTube](https://youtu.be/px1lLqGNeGA)

