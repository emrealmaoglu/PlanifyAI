import zipfile
import xml.etree.ElementTree as ET
import sys
import os

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as zf:
            xml_content = zf.read('word/document.xml')
        
        tree = ET.fromstring(xml_content)
        
        # Namespace map usually needed for docx
        namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        
        text_parts = []
        for node in tree.iter():
            if node.tag.endswith('}t'): # Text node
                if node.text:
                    text_parts.append(node.text)
            elif node.tag.endswith('}p'): # Paragraph node
                text_parts.append('\n')
                
        return ''.join(text_parts)
    except Exception as e:
        return f"Error reading {docx_path}: {str(e)}"

if __name__ == "__main__":
    files = sys.argv[1:]
    for f in files:
        print(f"\n{'='*50}\nFILE: {f}\n{'='*50}\n")
        print(extract_text_from_docx(f))
