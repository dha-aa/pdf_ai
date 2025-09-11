import os
import csv
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# 🔹 Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔹 Paths
txt_folder = "./txt_outputs"
output_folder = "./csv_outputs"
os.makedirs(output_folder, exist_ok=True)


def group_files():
    """Group text files by exam prefix (before _page_X)."""
    groups = defaultdict(list)

    if not os.path.exists(txt_folder):
        print(f" Folder {txt_folder} does not exist!")
        return groups

    for filename in os.listdir(txt_folder):
        if filename.endswith(".txt"):
            if "_page_" in filename:
                exam_prefix = filename.split("_page_")[0]
                groups[exam_prefix].append(filename)
            else:
                base_name = filename.replace(".txt", "")
                groups[base_name].append(filename)

    return groups


def extract_page_number(filename):
    """Extract page number from filename like _page_2.txt."""
    if "_page_" in filename:
        try:
            return int(filename.split("_page_")[1].split(".")[0])
        except (IndexError, ValueError):
            return 1
    return 1


def chunk_text_by_pages(sorted_files, max_pages_per_chunk=8):
    """Split exam into chunks of N pages each."""
    chunks = []
    current_chunk = []
    for i, filename in enumerate(sorted_files, 1):
        current_chunk.append(filename)
        if len(current_chunk) >= max_pages_per_chunk or i == len(sorted_files):
            chunks.append(current_chunk)
            current_chunk = []
    return chunks


def process_exam(exam_prefix, sorted_files):
    """Process exam in chunks so large exams don’t exceed context window."""
    all_csv_rows = []

    # 🔹 Split exam pages into manageable chunks
    file_chunks = chunk_text_by_pages(sorted_files, max_pages_per_chunk=8)

    for chunk_idx, file_chunk in enumerate(file_chunks, 1):
        combined_text = ""
        for filename in file_chunk:
            page_number = extract_page_number(filename)
            txt_path = os.path.join(txt_folder, filename)
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                print(f" Error reading {filename}: {e}")
                continue

            if not text.strip():
                continue

            combined_text += f"--- Page {page_number} ---\n{text}\n\n"

        if not combined_text.strip():
            continue

        # 🔹 Your detailed prompt with sample input/output
        prompt = f"""You are a CSV data extractor for medical exam papers. 
Convert the following MULTI-PAGE exam text into CSV format.

### OUTPUT FORMAT ###
Each row must follow this exact structure:
question,marks,paper_title,filename,page,year

### RULES ###
1. Use the exam heading (from the first page) as paper_title for ALL rows.
2. Extract EVERY question from ALL pages (including subparts a, b, c).
3. Clean questions: remove numbering, keep only the actual question text.
4. Set marks = 5 for each question unless stated otherwise.
5. Use filename: {exam_prefix}.pdf
6. Use the correct page number (from the markers like --- Page 2 ---).
7. Extract year from the exam date in the heading (e.g., "March 1990" → 1990).
8. Put quotes around fields that contain commas.
9. Output ONLY CSV rows (no headers, no notes).

### SAMPLE INPUT ###
--- Page 1 ---
M.S. DEGREE EXAMINATION, March 1990
General Surgery – Applied Basic Sciences
1. Describe the surgical anatomy of the thyroid gland.
2. Write notes on: (a) Deep palmar spaces. (b) Femoral canal.

--- Page 2 ---
PHYSIOLOGY
(a) Pain pathway
(b) Cardiac cycle

### SAMPLE OUTPUT ###
"Describe the surgical anatomy of the thyroid gland",5,"M.S. DEGREE EXAMINATION, March 1990 – General Surgery – Applied Basic Sciences","{exam_prefix}.pdf",1,1990
"Write notes on: Deep palmar spaces",5,"M.S. DEGREE EXAMINATION, March 1990 – General Surgery – Applied Basic Sciences","{exam_prefix}.pdf",1,1990
"Write notes on: Femoral canal",5,"M.S. DEGREE EXAMINATION, March 1990 – General Surgery – Applied Basic Sciences","{exam_prefix}.pdf",1,1990
"Pain pathway",5,"M.S. DEGREE EXAMINATION, March 1990 – General Surgery – Applied Basic Sciences","{exam_prefix}.pdf",2,1990
"Cardiac cycle",5,"M.S. DEGREE EXAMINATION, March 1990 – General Surgery – Applied Basic Sciences","{exam_prefix}.pdf",2,1990

### TEXT TO CONVERT (chunk {chunk_idx}) ###
{combined_text}

### CSV OUTPUT ###
"""

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # or gpt-4o-mini if available
                messages=[
                    {"role": "system", "content": "You are a precise CSV data extractor. Output only valid CSV rows."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=3000,
            )
            chunk_csv = response.choices[0].message.content.strip()  # type: ignore
            if chunk_csv:
                all_csv_rows.append(chunk_csv)
                print(f" ✅ Processed chunk {chunk_idx}/{len(file_chunks)} for {exam_prefix}")
        except Exception as e:
            print(f" API Error for {exam_prefix}, chunk {chunk_idx}: {e}")
            continue

    return "\n".join(all_csv_rows)


def save_individual_csv(exam_prefix, csv_output):
    """Save extracted CSV for one exam."""
    if not csv_output.strip():
        print(f" No data for {exam_prefix}")
        return False

    output_csv = os.path.join(output_folder, f"{exam_prefix}.csv")
    try:
        with open(output_csv, "w", encoding="utf-8", newline="") as f:
            f.write("question,marks,paper_title,filename,page,year\n")
            f.write(csv_output + "\n")

        count = csv_output.count("\n") + 1
        print(f" Saved {output_csv} ({count} questions)")
        return True
    except Exception as e:
        print(f" Error saving {output_csv}: {e}")
        return False


def save_combined_csv(all_exam_data):
    """Save one combined CSV with all exams merged."""
    combined_csv = os.path.join(output_folder, "all_exams_combined.csv")
    try:
        with open(combined_csv, "w", encoding="utf-8", newline="") as f:
            f.write("question,marks,paper_title,filename,page,year\n")
            total_questions = 0
            for exam_prefix, csv_output in all_exam_data.items():
                for row in csv_output.splitlines():
                    if row.strip():
                        f.write(row + "\n")
                        total_questions += 1
        print(f" Combined CSV saved: {combined_csv} ({total_questions} total questions)")
        return True
    except Exception as e:
        print(f" Error saving combined CSV: {e}")
        return False


def main():
    print("Starting multi-page exam processing...")

    groups = group_files()
    if not groups:
        print("No text files found!")
        return

    print(f"Found {len(groups)} exam groups")

    all_exam_data = {}

    for exam_prefix, files in groups.items():
        sorted_files = sorted(files, key=extract_page_number)
        print(f"\nProcessing exam {exam_prefix} ({len(sorted_files)} pages)")
        csv_output = process_exam(exam_prefix, sorted_files)
        if save_individual_csv(exam_prefix, csv_output):
            all_exam_data[exam_prefix] = csv_output

    if all_exam_data:
        save_combined_csv(all_exam_data)


if __name__ == "__main__":
    main()
