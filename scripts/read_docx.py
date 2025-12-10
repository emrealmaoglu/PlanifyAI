
import zipfile
import xml.etree.ElementTree as ET
import sys
import os

def extract_text_from_docx(docx_path):
    """
    Extracts text from a .docx file by reading word/document.xml from the zip archive.
    This avoids dependencies like python-docx.
    """
    try:
        with zipfile.ZipFile(docx_path) as zf:
            xml_content = zf.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Namespace for Word Processing ML
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            text_parts = []
            # Find all text nodes (<w:t>)
            for node in tree.iter():
                if node.tag.endswith('}t'):
                    if node.text:
                        text_parts.append(node.text)
                elif node.tag.endswith('}p'):
                    # Add newline after paragraphs
                    text_parts.append('\n')
            
            return "".join(text_parts)
    except Exception as e:
        return f"Error reading {docx_path}: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_docx.py <path_to_docx>")
        sys.exit(1)
        
    path = sys.argv[1]
    if os.path.exists(path):
        print(extract_text_from_docx(path))
    else:
        print(f"File not found: {path}")
