from docling.document_converter import DocumentConverter
from pathlib import Path
import pprint
import os

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = 'block'
##this works
# wat wil ik dat het doet?
## 
source = Path('C:/Users/m.venema/Desktop/metadata_script/src/eDepot_FAQ.pdf')  # file path or URL
converter = DocumentConverter()
doc = converter.convert(source).document
pprint.pprint(doc)
doc.save_as_markdown("C:/Users/m.venema/Desktop/test/docling.md")


##converts docs to text
#def doc_converter():
#    