# POC 2: File Upload with PyPDF2 and pdfplumber

## Overview

This POC tests PDF file upload and processing in Reflex using PyPDF2 and pdfplumber libraries.

## Critical Requirements

1. Upload PDF files (5-10 MB)
2. Display upload progress
3. Extract text with PyPDF2 (for EDW pairing analysis)
4. Extract text with pdfplumber (for bid line analysis)
5. Handle errors gracefully
6. Measure performance metrics

## Success Criteria

- ✅ File upload widget works
- ✅ PDF text extraction successful with PyPDF2
- ✅ PDF text extraction successful with pdfplumber
- ✅ Progress indicator during processing
- ✅ Error handling for invalid files
- ✅ Memory usage measured
- ✅ Upload/processing time measured

## Running the POC

```bash
# Navigate to POC directory
cd phase0_pocs/file_upload

# Activate virtual environment
source ../../.venv/bin/activate

# Install dependencies (if not already installed)
pip install psutil

# Initialize Reflex (already done)
# reflex init

# Run the POC
reflex run

# Access in browser
open http://localhost:3000
```

## Test Files

Two sample PDFs are provided in the `test_pdfs/` directory:
- `pairing_sample.pdf` (1.4 MB) - Trip pairing PDF for testing PyPDF2
- `bidline_sample.pdf` (2.7 MB) - Bid line PDF for testing pdfplumber

## Testing Instructions

1. Upload one of the test PDFs using the drag-and-drop or file picker
2. Click "Upload" button
3. Observe:
   - Upload progress indicator (0% → 100%)
   - File info (name, size, page count)
   - Performance metrics (processing time, memory usage)
   - Extracted text from both PyPDF2 and pdfplumber (first 3 pages)
4. Try uploading both files to compare performance
5. Try uploading a non-PDF file to test error handling

## Implementation Details

### Libraries Used
- **reflex**: Web framework
- **PyPDF2**: PDF text extraction (used by EDW reporter)
- **pdfplumber**: PDF text and table extraction (used by bid line parser)
- **psutil**: Memory usage monitoring

### Key Features
- Async file upload handling
- Progress tracking (0%, 10%, 20%, 50%, 60%, 90%, 100%)
- Dual library testing (PyPDF2 + pdfplumber)
- Performance metrics:
  - Processing time for each library
  - Memory usage delta
  - Page count
- Error handling per library (graceful degradation)
- First 3 pages extracted (500 chars per page preview)

### File Structure

```
file_upload/
├── poc_file_upload/
│   ├── __init__.py              # Package init
│   └── poc_file_upload.py       # Main POC application
├── test_pdfs/
│   ├── pairing_sample.pdf       # Test file (1.4 MB)
│   └── bidline_sample.pdf       # Test file (2.7 MB)
├── rxconfig.py                  # Reflex configuration
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Expected Results

### Performance Expectations
- **Upload time**: < 5 seconds for 5 MB file
- **PyPDF2 processing**: < 2 seconds for 50 pages
- **pdfplumber processing**: < 3 seconds for 50 pages
- **Memory usage**: < 200 MB for 10 MB file

### Success Indicators
- ✅ Both libraries extract readable text
- ✅ Processing completes without errors
- ✅ Performance meets expectations
- ✅ Error messages are clear and helpful
- ✅ Progress indicator works smoothly

## Risk Assessment

**Risk Level:** 🟢 LOW

**Rationale:**
- Reflex has built-in file upload widget (`rx.upload()`)
- PyPDF2 and pdfplumber are mature, well-tested libraries
- Both libraries already used successfully in Streamlit app
- No anticipated compatibility issues

## Next Steps

After POC 2 passes:
1. Document findings in `docs/phase0_poc2_findings.md`
2. Proceed to POC 3: Plotly Charts (Day 4)
3. Update Phase 0 overall assessment

## Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'psutil'`
- **Solution:** Run `pip install psutil`

**Issue:** Port 3000 already in use
- **Solution:** Reflex will auto-increment to 3001, 3002, etc.

**Issue:** PDF upload fails
- **Solution:** Check file is actually a PDF and < 50 MB

**Issue:** No text extracted
- **Solution:** PDF may be image-based (scanned), requires OCR

## Documentation

See `docs/phase0_poc2_findings.md` for detailed test results and findings (will be created after testing).
