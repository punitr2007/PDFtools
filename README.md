<div align="center">

# 📑 PDFtools

### *Smart Image-to-Sorted-PDF Builder Powered by OCR & Heuristic Sorting*

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![OCR: Tesseract](https://img.shields.io/badge/OCR-Tesseract_5-blue?style=for-the-badge&logo=google)](https://github.com/tesseract-ocr/tesseract)
[![Pillow](https://img.shields.io/badge/Engine-Pillow-green?style=for-the-badge)](https://python-pillow.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20|%20macOS%20|%20Windows-lightgrey?style=for-the-badge)]()

<p align="center">
  <b>Never sort disorganized screenshots or assignment questions manually again.</b><br>
  PDFtools scans unordered screenshots, extracts question numbers via OCR & multi-tiered regex heuristics, sorts them in exact sequential numerical order, and compiles them into a clean, presentation-grade PDF.
</p>

</div>

---

## ⚡ Highlights

- 🔍 **Intelligent Question Extraction**: Automatically detects question patterns (`1.`, `Q1`, `Question 1:`, `1)`, `(1)`, `[1]`, `1,`) directly from image text.
- 🔢 **Natural Numerical Sorting**: Correctly sequences multi-digit questions (`Q1, Q2, ..., Q9, Q10, Q11`) rather than alphabetical sorting (`Q1, Q10, Q11, Q2`).
- 📐 **Adaptive Layout Modes**:
  - `native`: Preserves the pixel-perfect original resolution and aspect ratio of screenshots without quality loss.
  - `a4-landscape`: Fits images onto standardized A4 Landscape pages (1754×1240) with margin centering.
  - `a4-portrait`: Fits images onto standardized A4 Portrait pages (1240×1754) with margin centering.
- 🛡️ **Self-Healing OCR Setup**: Automatically finds system Tesseract installations, detects local `tessdata`, or downloads the required `eng.traineddata` model on-the-fly.
- 👁️ **Dry-Run Preview**: Preview detected question numbers, source files, and text snippets in a CLI table before writing files.
- 🚀 **Robust Format & Path Resolution**: Handles directories, relative paths, and automatic extension resolution with zero risk of file corruption.

---

## 🧠 How It Works

```mermaid
flowchart TD
    A[Unordered Image Batch\n.png, .jpg, .webp, .bmp] --> B[Image Preprocessing & Normalization]
    B --> C[Tesseract OCR Engine]
    C --> D[Multi-Tier Question Extractor]
    
    subgraph Heuristic Matching
        D --> E1[Tier 1: Top-5 Line Headers\ne.g., '1.', 'Q1', '(1)', '1,']
        D --> E2[Tier 2: Body Paragraph Patterns\ne.g., '14. Neha and Priya...']
        D --> E3[Tier 3: Filename Regex Fallback\ne.g., 'Screenshot_Q4.png']
    end

    E1 --> F[Natural Numerical Key Evaluator]
    E2 --> F
    E3 --> F

    F --> G[Sorted Sequence Generator]
    G --> H[Layout & Canvas Engine\nNative / A4 Landscape / A4 Portrait]
    H --> I[High-Quality Optimized PDF Output]
```

---

## 📦 Installation & Prerequisites

### 1. System Requirements (Tesseract OCR)

Ensure Tesseract OCR is installed on your system:

- **Debian / Ubuntu / Kali**:
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr
  ```
- **Arch Linux / Manjaro**:
  ```bash
  sudo pacman -S tesseract
  ```
- **macOS** (Homebrew):
  ```bash
  brew install tesseract
  ```
- **Windows**:
  Download and install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).

### 2. Python Dependencies

Clone the repository and install required packages:

```bash
git clone git@github.com:punitr2007/PDFtools.git
cd PDFtools
pip install -r requirements.txt
```

---

## 🚀 Usage Guide

### 1. Preview Detected Sequence (Dry-Run)
Inspect what question numbers were found and their assigned order without creating a PDF:
```bash
python3 create_sorted_pdf.py -i ./Images --preview
```

**Output Table Preview:**
```text
==========================================================================================
Page   | Detected Q#  | Source Image                     | Question Snippet                
------------------------------------------------------------------------------------------
1      | Q1           | Screenshot_20260912_160832.png   | 1. Meera recently started usi...
2      | Q2           | Screenshot_20260912_160847.png   | 2. Suraj decides to improve h...
3      | Q3           | Screenshot_20260912_160856.png   | 3. Rohan, a first-year engine...
4      | Q4           | Screenshot_20260912_160902.png   | 4, Salman is riding his bike ...
...
23     | Q24          | Screenshot_20260912_161046.png   | 24. Sanaya became upset after...
==========================================================================================
```

### 2. Basic Compilation (Native Resolution)
```bash
python3 create_sorted_pdf.py -i ./Images -o Assignment_Sorted.pdf
```

### 3. Generate A4 Landscape Presentation PDF
```bash
python3 create_sorted_pdf.py -i ./Images -o Assignment_A4.pdf --layout a4-landscape
```

### 4. Reverse Ordering (Descending)
```bash
python3 create_sorted_pdf.py -i ./Images -o Assignment_Desc.pdf --reverse
```

### 5. Custom Tessdata Directory
```bash
python3 create_sorted_pdf.py -i ./Images --tessdata /path/to/tessdata
```

---

## 🛠️ CLI Reference

| Parameter | Flag | Default | Description |
|---|---|---|---|
| **Input Directory** | `-i`, `--input-dir` | `./Images` | Directory containing screenshots/images to process |
| **Output File** | `-o`, `--output` | `<input_name>_Sorted.pdf` | Destination path for the generated PDF (file or directory) |
| **Page Layout** | `--layout` | `native` | Layout format: `native`, `a4-landscape`, `a4-portrait` |
| **Dry-run Preview** | `--preview`, `--dry-run` | `False` | Displays the detected question table without generating the PDF |
| **Reverse Sort** | `--reverse` | `False` | Sorts pages in descending numerical order |
| **Custom Tessdata** | `--tessdata` | `None` (Auto) | Path to custom Tesseract language model directory |

---

## 🔮 Future Scope & Next-Level Roadmap

To evolve **PDFtools** from a standalone CLI script into an end-to-end Intelligent Document Platform, the following enhancements are planned:

### 1. 🤖 Multimodal AI & Vision LLM Fallback (VLM)
- **Local & Cloud VLM Support**: Integrate lightweight vision models (e.g. `Qwen2-VL`, `MiniCPM-V`, or `Gemini Flash API` / `Ollama`) to handle complex handwritten exam sheets, curved text, rotated screenshots, and stylized question headers where classical OCR fails.
- **Smart Schema Extractor**: Extract question metadata (marks, topic tags, difficulty, sub-parts `(a)`, `(b)`) into structured JSON alongside the PDF.

### 2. 🖥️ Interactive Web UI & Drag-and-Drop GUI
- **Modern Web Dashboard**: Fast React/Vite + FastAPI web interface allowing users to upload a ZIP or folder of screenshots.
- **Interactive Visual Sorter**: Live thumbnail grid with auto-detected question tags that users can drag-and-drop to reorder before PDF export.
- **Side-by-Side OCR Inspector**: Highlight bounding boxes on image hover to inspect OCR confidence.

### 3. 📄 Advanced PDF Engineering & Processing
- **Searchable Sandwich PDFs**: Embed an invisible OCR text layer underneath each image, making the final PDF fully searchable, selectable, and copy-pasteable.
- **Auto De-skew & Crop**: Computer vision algorithms (OpenCV) to auto-crop browser margins, status bars, and auto-straighten tilted camera photos.
- **Page De-duplication**: Perceptual hashing (pHash) to detect and remove accidental duplicate screenshots.
- **Header/Footer Watermarking**: Add customizable page numbers (`Page X of Y`), assignment titles, or institute watermarks.

### 4. ⚡ Integrations & Automation
- **Browser Extension**: 1-click capture extension to screenshot assignment questions directly in browser tabs and compile them into a sorted PDF instantly.
- **Telegram / Discord Bot**: Send a batch of screenshots to a bot and receive a sorted, indexed PDF in seconds.
- **Cross-Platform Standalone Binary**: Package with PyInstaller or Nuitka for 1-click executable usage without requiring Python installation.

---

## 🤝 Contributing

Contributions are warmly welcome!
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

Developed with ❤️ by [Punit Ranjan](https://github.com/punitr2007).
