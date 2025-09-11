import os
import io
import fitz
import pytesseract
from PIL import Image
from tqdm import tqdm

PDF_FOLDER = "./pdfs"
OUTPUT_FOLDER = "./txt_outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

SAVE_MODE = "separate"  # or "combined"


def extract_text_from_pdf(pdf_path: str, output_folder: str, save_mode: str = "combined") -> str:
    filename = os.path.splitext(os.path.basename(pdf_path))[0]

    try:
        document = fitz.open(pdf_path)
    except Exception as e:
        return f" Failed to open {pdf_path}: {e}"

    extracted_text = []

    # Per-page progress bar
    for page_num in tqdm(range(document.page_count), desc=f"Processing {filename}", unit="page"):
        page = document[page_num]
        page_text = page.get_text().strip() # type: ignore

        # OCR images
        ocr_texts = []
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = document.extract_image(xref)
            image_bytes = base_image.get("image")
            if image_bytes:
                with Image.open(io.BytesIO(image_bytes)) as image:
                    text_from_image = pytesseract.image_to_string(image).strip()
                    if text_from_image:
                        ocr_texts.append(text_from_image)

        combined_text = page_text
        if ocr_texts:
            combined_text += "\n\n" + "\n\n".join(ocr_texts)

        # Save per mode
        if save_mode == "separate":
            page_file = os.path.join(output_folder, f"{filename}_page_{page_num + 1}.txt")
            with open(page_file, "w", encoding="utf-8") as f:
                f.write(combined_text)
        else:
            extracted_text.append(f"\n\n--- Page {page_num + 1} ---\n{combined_text}")

    document.close()

    if save_mode == "combined" and extracted_text:
        output_file = os.path.join(output_folder, f"{filename}.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(extracted_text))

    return f"Processed: {filename} ({save_mode})"


def process_all_pdfs(pdf_folder: str, output_folder: str, save_mode: str = "combined"):
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    for pdf in tqdm(pdf_files, desc="Overall PDFs", unit="pdf"):
        pdf_path = os.path.join(pdf_folder, pdf)
        result = extract_text_from_pdf(pdf_path, output_folder, save_mode)
        print(result)

    print(" All PDFs processed successfully!")


if __name__ == "__main__":
    process_all_pdfs(PDF_FOLDER, OUTPUT_FOLDER, SAVE_MODE)
