import os
import subprocess
import sys
import glob

def get_files():
    # consistent sorting
    files = sorted(glob.glob("/Users/emrealmaoglu/Desktop/PlanifyAI/docs/research/*.docx") + glob.glob("/Users/emrealmaoglu/Desktop/PlanifyAI/docs/research/*.md"))
    # filter out the ones we generated
    files = [f for f in files if "RESEARCH_EXTRACTOR_TODO" not in f and "RESEARCH_KNOWLEDGE_BASE" not in f and "OPTIMIZATION_SUMMARY" not in f]
    return files

def extract_text(filepath):
    if filepath.endswith(".docx"):
        result = subprocess.run(["textutil", "-convert", "txt", filepath, "-stdout"], capture_output=True, text=True)
        return result.stdout
    else:
        with open(filepath, "r") as f:
            return f.read()

def main():
    offset = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    all_files = get_files()
    if offset >= len(all_files):
        print("DONE")
        return

    batch_files = all_files[offset:offset+batch_size]
    
    print(f"--- BATCH INFO: Files {offset} to {offset+len(batch_files)} of {len(all_files)} ---")
    for f in batch_files:
        filename = os.path.basename(f)
        print(f"\n\n$$$ FILE_START: {filename} $$$")
        try:
            content = extract_text(f)
            # strictly limit content length per file to avoid context explosion if huge
            # but user said "suyunu sık", so I need full content. 
            # I will trust the batch size of 3-5 to fit in context.
            print(content)
        except Exception as e:
            print(f"ERROR reading {filename}: {e}")
        print(f"$$$ FILE_END: {filename} $$$")

if __name__ == "__main__":
    main()
