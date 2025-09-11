import os
import csv
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# 🔹 Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔹 Paths
txt_folder = "./txt_outputs"
output_folder = "./csv_outputs"
os.makedirs(output_folder, exist_ok=True)

# 🔹 Group files by exam prefix (everything before "_page_X")
def group_files():
    """Group text files by exam prefix"""
    groups = defaultdict(list)
    
    if not os.path.exists(txt_folder):
        print(f" Folder {txt_folder} does not exist!")
        return groups
    
    for filename in os.listdir(txt_folder):
        if filename.endswith(".txt"):
            if "_page_" in filename:
                exam_prefix = filename.split("_page_")[0]  # e.g. "222214KQ (1)"
                groups[exam_prefix].append(filename)
            else:
                # Handle files without _page_ structure
                base_name = filename.replace(".txt", "")
                groups[base_name].append(filename)
    
    return groups

def extract_page_number(filename):
    """Extract page number from filename"""
    if "_page_" in filename:
        try:
            return int(filename.split("_page_")[1].split(".")[0])
        except (IndexError, ValueError):
            return 1
    return 1

def process_page(exam_prefix, filename, page_number):
    """Process one page and return its CSV output."""
    txt_path = os.path.join(txt_folder, filename)
    
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f" Error reading {filename}: {e}")
        return filename, ""

    # Clean and validate text
    if not text.strip():
        print(f" Empty file: {filename}")
        return filename, ""

    prompt = f"""You are a CSV data extractor for medical exam papers. Convert the following exam text into CSV format.

### OUTPUT FORMAT ###
Each row must follow this exact structure:
question,marks,paper_title,filename,page,year

### EXTRACTION RULES ###
1. Extract EVERY question from the text (including sub-parts like (a), (b), etc.)
2. Clean questions: remove numbering (1., 2., etc.) and section letters, keep only the actual question text
3. Set marks = 5 for each question (unless explicitly stated otherwise)
4. Extract paper title from the exam heading exactly as written
   Examples: 
   - "M.S. Degree Examination, March 1990 – General Surgery – Applied Basic Sciences"
   - "M.S. DEGREE EXAMINATION, OCTOBER 1990 Branch I — General Surgery Part I"
5. Use filename: {exam_prefix}.pdf
6. Use page: {page_number}
7. Extract year from the exam date (e.g., March 1990 → 1990, October 1990 → 1990)
8. Put quotes around fields that contain commas
9. Output ONLY CSV rows - no headers, no explanations, no extra text

### SAMPLE INPUT ###
"1. Describe the surgical anatomy of the thyroid gland.
2. Write notes on: (a) Deep palmar spaces. (b) Femoral canal."

### SAMPLE OUTPUT ###
"Describe the surgical anatomy of the thyroid gland",5,"M.S. Degree Examination, March 1990 – General Surgery","{exam_prefix}.pdf",{page_number},1990
"Write notes on: Deep palmar spaces",5,"M.S. Degree Examination, March 1990 – General Surgery","{exam_prefix}.pdf",{page_number},1990
"Write notes on: Femoral canal",5,"M.S. Degree Examination, March 1990 – General Surgery","{exam_prefix}.pdf",{page_number},1990

### TEXT TO CONVERT ###
{text}

### CSV OUTPUT ###"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Fixed model name
            messages=[
                {"role": "system", "content": "You are a precise CSV data extractor. Output only clean CSV rows with no extra text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        csv_output = response.choices[0].message.content.strip() # type: ignore
        return filename, csv_output
        
    except Exception as e:
        print(f" API Error for {filename}: {e}")
        return filename, ""

def validate_csv_row(row):
    """Validate and clean CSV row"""
    # Remove empty lines and non-CSV content
    if not row.strip():
        return None
    
    # Skip rows that don't look like CSV (common LLM mistakes)
    if row.startswith("#") or row.startswith("Note:") or "CSV OUTPUT" in row:
        return None
    
    # Basic CSV validation - should have at least 5 commas for 6 fields
    comma_count = row.count(',')
    if comma_count < 5:
        return None
    
    return row.strip()

def merge_csv_data(results, sorted_files):
    """Merge CSV data from multiple files"""
    all_rows = []
    header = "question,marks,paper_title,filename,page,year"
    all_rows.append(header)
    
    for filename in sorted_files:
        if filename in results and results[filename]:
            rows = results[filename].splitlines()
            for row in rows:
                cleaned_row = validate_csv_row(row)
                if cleaned_row:
                    all_rows.append(cleaned_row)
    
    return all_rows

def save_individual_csv(exam_prefix, all_rows):
    """Save CSV file for one exam"""
    output_csv = os.path.join(output_folder, f"{exam_prefix}.csv")
    
    try:
        with open(output_csv, "w", encoding="utf-8", newline='') as f:
            for row in all_rows:
                f.write(row + "\n")
        
        question_count = len(all_rows) - 1  # Subtract header
        print(f" Saved: {output_csv} ({question_count} questions)")
        return True
        
    except Exception as e:
        print(f" Error saving {output_csv}: {e}")
        return False

def save_combined_csv(all_exam_data):
    """Save one combined CSV with all exams"""
    combined_csv = os.path.join(output_folder, "all_exams_combined.csv")
    
    try:
        with open(combined_csv, "w", encoding="utf-8", newline='') as f:
            # Write header once
            f.write("question,marks,paper_title,filename,page,year\n")
            
            total_questions = 0
            for exam_prefix, rows in all_exam_data.items():
                # Skip header row from individual exams
                for row in rows[1:]:
                    if row.strip():
                        f.write(row + "\n")
                        total_questions += 1
        
        print(f"Combined CSV saved: {combined_csv} ({total_questions} total questions)")
        return True
        
    except Exception as e:
        print(f"Error saving combined CSV: {e}")
        return False

# 🔹 Main processing
def main():
    print("Starting Text to CSV conversion with OpenAI...")
    
    # Group files
    groups = group_files()
    if not groups:
        print("No text files found to process!")
        return
    
    print(f"Found {len(groups)} exam groups")
    
    all_exam_data = {}
    successful_conversions = 0
    
    # Process each exam group
    for exam_prefix, files in groups.items():
        print(f"\nProcessing exam: {exam_prefix} ({len(files)} pages)")
        
        # Sort files by page number
        sorted_files = sorted(files, key=extract_page_number)
        
        results = {}
        
        # Process pages with threading
        with ThreadPoolExecutor(max_workers=3) as executor:  # Reduced workers to avoid rate limits
            futures = {
                executor.submit(
                    process_page, 
                    exam_prefix, 
                    filename, 
                    extract_page_number(filename)
                ): filename
                for filename in sorted_files
            }
            
            for future in tqdm(as_completed(futures), total=len(futures), 
                              desc=f"Processing {exam_prefix}", unit="page"):
                try:
                    filename, csv_output = future.result()
                    results[filename] = csv_output
                except Exception as e:
                    print(f"Error processing future: {e}")
        
        # Merge results
        all_rows = merge_csv_data(results, sorted_files)
        
        if len(all_rows) > 1:  # More than just header
            if save_individual_csv(exam_prefix, all_rows):
                all_exam_data[exam_prefix] = all_rows
                successful_conversions += 1
        else:
            print(f"No valid data extracted for {exam_prefix}")
    
    # Save combined CSV
    if all_exam_data:
        save_combined_csv(all_exam_data)
    
    print(f"\n Conversion complete! Successfully processed {successful_conversions}/{len(groups)} exams")
    print(f"Output folder: {output_folder}")

if __name__ == "__main__":
    main()