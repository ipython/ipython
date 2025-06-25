# List of PDFs in order with titles for bookmarks
doc_files = [
    ("/mnt/data/1. Cover Letter - Table of Contents New.pages.pdf", "Cover Letter - Table of Contents"),
    ("/mnt/data/2. cover Letter new.pages.pdf", "Cover Letter"),
    ("/mnt/data/3. Ex Parte Application.pages.pdf", "Ex Parte Application"),
    ("/mnt/data/4. Notice of Ex .Parte Hearing.pages.pdf", "Notice of Ex Parte Hearing"),
    ("/mnt/data/5. Fee Waver FW-001F .pdf", "Fee Waiver FW-001F"),
    ("/mnt/data/6 Proposed Order on Ex Parte Applicaton.pages.pdf", "Proposed Order on Ex Parte Application"),
    ("/mnt/data/7. Remote app. RA- 015.pdf", "Remote App RA-015"),
    ("/mnt/data/8. Summary of Ex Parta.pages.pdf", "Summary of Ex Parte"),
    ("/mnt/data/9. Summary of Supplimental Package.pages.pdf", "Summary of Supplemental Package"),
    ("/mnt/data/10. Exihibits Cover page .pages.pdf", "Exhibits Cover Page"),
    ("/mnt/data/11. Exhibit A.pages.pdf", "Exhibit A"),
]

# Merge PDFs with bookmarks
merger = PdfMerger()
page_counter = 0
for filepath, title in doc_files:
    reader = PdfReader(filepath)
    num_pages = len(reader.pages)
    merger.append(filepath, import_bookmarks=False)
    merger.addBookmark(title, page_counter)
    page_counter += num_pages
merger.write("/mnt/data/Combined_Court_Document.pdf")
merger.close()

# Create ZIP
zip_path = "/mnt/data/Combined_Court_Document.zip"
with zipfile.ZipFile(zip_path, "w") as zf:
    zf.write("/mnt/data/Combined_Court_Document.pdf", arcname="Combined_Court_Document.pdf")

# Provide download link
FileLink(zip_path)
```
