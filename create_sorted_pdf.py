#!/usr/bin/env python3
"""

# Basic usage
python3 create_sorted_pdf.py -i /path/to/Images -o /path/to/Output.pdf

# Preview order without generating PDF
python3 create_sorted_pdf.py -i /path/to/Images --preview


Sorted Image-to-PDF Builder (PDFtools)
=====================================
Automatically extracts question numbers or ordering patterns from screenshots/images
using OCR and natural language heuristics, sorts them in proper sequential order,
and compiles them into a high-quality PDF.
"""

import argparse
import os
import re
import sys
import glob
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image


def get_tessdata_path() -> Optional[str]:
    """Find or download local tessdata directory if not present in system."""
    script_dir = Path(__file__).resolve().parent
    local_tessdata = script_dir / "tessdata"
    
    # 1. Check local tessdata directory
    if local_tessdata.exists() and (local_tessdata / "eng.traineddata").exists():
        return str(local_tessdata)
        
    # 2. Check TESSDATA_PREFIX environment variable
    if "TESSDATA_PREFIX" in os.environ and os.path.exists(os.environ["TESSDATA_PREFIX"]):
        tess_path = Path(os.environ["TESSDATA_PREFIX"])
        if (tess_path / "eng.traineddata").exists() or (tess_path / "tessdata" / "eng.traineddata").exists():
            return str(tess_path)
            
    # 3. Check standard system locations
    system_locations = [
        Path("/usr/share/tessdata"),
        Path("/usr/share/tesseract-ocr/4.00/tessdata"),
        Path("/usr/share/tesseract-ocr/5/tessdata"),
        Path("/usr/local/share/tessdata"),
    ]
    for loc in system_locations:
        if (loc / "eng.traineddata").exists():
            return str(loc)
            
    # 4. Attempt automatic download into local directory if curl is available
    try:
        local_tessdata.mkdir(parents=True, exist_ok=True)
        target_file = local_tessdata / "eng.traineddata"
        print("[*] Downloading eng.traineddata OCR model to local tessdata directory...")
        res = subprocess.run(
            ["curl", "-L", "-s", "-o", str(target_file), "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata"],
            capture_output=True,
            timeout=30
        )
        if res.returncode == 0 and target_file.exists() and target_file.stat().st_size > 1000:
            print("[+] Successfully downloaded eng.traineddata.")
            return str(local_tessdata)
    except Exception as e:
        print(f"[!] Warning: Could not download tessdata automatically: {e}", file=sys.stderr)
        
    return None


def run_ocr(image_path: str, tessdata_dir: Optional[str] = None) -> str:
    """Run Tesseract OCR on an image and return recognized text."""
    env = os.environ.copy()
    if tessdata_dir:
        env["TESSDATA_PREFIX"] = tessdata_dir

    try:
        cmd = ["tesseract", image_path, "stdout", "--psm", "6"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
            
        # Fallback to default page segmentation mode
        cmd_fallback = ["tesseract", image_path, "stdout"]
        res_fb = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        if res_fb.returncode == 0:
            return res_fb.stdout.strip()
    except FileNotFoundError:
        print("[!] 'tesseract' binary not found. Falling back to filename sort.", file=sys.stderr)
    except Exception as e:
        print(f"[!] OCR error for {image_path}: {e}", file=sys.stderr)
        
    return ""


def extract_question_number(text: str, filename: str) -> Tuple[Optional[float], str]:
    """
    Extracts question number from OCR text or falls back to filename.
    Returns (sort_key, snippet).
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    snippet = lines[0] if lines else ""

    # Strategy 1: Look at the first 5 lines for leading question patterns
    # e.g. "1.", "1)", "1:", "1 -", "1,", "(1)", "[1]"
    for line in lines[:5]:
        # Handle "(1)", "[1]"
        m_bracket = re.match(r"^[\[\(](\d{1,4})(?:\.(\d+))?[\]\)]", line)
        if m_bracket:
            major = int(m_bracket.group(1))
            minor = int(m_bracket.group(2)) if m_bracket.group(2) else 0
            val = major + (minor * 0.01)
            return val, line

        # Handle "1.", "1,", "1:", "1)", "1-"
        m = re.match(r"^(\d{1,4})(?:\.(\d+))?\s*[\.\,\:\)\-]", line)
        if m:
            major = int(m.group(1))
            minor = int(m.group(2)) if m.group(2) else 0
            val = major + (minor * 0.01)
            return val, line

        # e.g. "Question 1", "Q1", "Que 1", "Problem 1", "Q.1", "Q-1"
        m_q = re.match(r"^(?:Question|Q|Que|Ques|Prob|Problem)\s*[\.\,\:\-\#]?\s*(\d{1,4})(?:\.(\d+))?", line, re.IGNORECASE)
        if m_q:
            major = int(m_q.group(1))
            minor = int(m_q.group(2)) if m_q.group(2) else 0
            val = major + (minor * 0.01)
            return val, line

    # Strategy 2: Search anywhere in OCR text for beginning-of-paragraph question indicators (supporting . , : ) )
    m_any = re.search(r"(?:^|\n)\s*(\d{1,4})(?:\.(\d+))?\s*[\.\,\:\)]\s+[A-Za-z]", text)
    if m_any:
        major = int(m_any.group(1))
        minor = int(m_any.group(2)) if m_any.group(2) else 0
        val = major + (minor * 0.01)
        return val, m_any.group(0).strip().replace("\n", " ")

    # Strategy 3: Search within filename (e.g. Q1_screenshot.png, 1_img.png)
    base_name = Path(filename).stem
    m_fn = re.search(r"(?:^|[_\-\s]|q|question)(\d{1,4})(?:[_\-\s]|$)", base_name, re.IGNORECASE)
    if m_fn:
        return float(m_fn.group(1)), f"[Filename match: {base_name}]"

    return None, snippet


def natural_sort_key(s: str) -> List[Any]:
    """Natural alphanumeric sort key for strings."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def collect_and_sort_images(
    input_dir: str,
    reverse: bool = False,
    tessdata_dir: Optional[str] = None,
    extensions: Tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")
) -> List[Dict[str, Any]]:
    """
    Finds all images in directory, extracts question numbers via OCR,
    and returns a sorted list of image metadata dictionaries.
    """
    input_path = Path(input_dir).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")

    image_files = []
    for ext in extensions:
        image_files.extend(input_path.glob(f"*{ext}"))
        image_files.extend(input_path.glob(f"*{ext.upper()}"))
        
    image_files = sorted(list(set(image_files)), key=lambda p: natural_sort_key(p.name))
    if not image_files:
        raise ValueError(f"No supported images found in {input_path}")

    print(f"[*] Found {len(image_files)} image(s) in {input_path}")
    print("[*] Performing OCR & Question Number Extraction...")

    records = []
    for idx, img_p in enumerate(image_files, 1):
        ocr_text = run_ocr(str(img_p), tessdata_dir)
        qnum, snippet = extract_question_number(ocr_text, img_p.name)
        
        records.append({
            "path": str(img_p),
            "filename": img_p.name,
            "qnum": qnum,
            "sort_key": qnum if qnum is not None else 999999 + idx,
            "snippet": snippet,
            "ocr_text": ocr_text
        })

    # Sort primarily by question number (or fallback key), then filename naturally
    records.sort(key=lambda r: (r["sort_key"], natural_sort_key(r["filename"])), reverse=reverse)
    return records


def create_pdf(
    sorted_records: List[Dict[str, Any]],
    output_pdf_path: str,
    page_layout: str = "native"
) -> str:
    """
    Assembles sorted images into a single PDF.
    
    Layout modes:
      - 'native': Exact original image resolution/aspect ratio for each page.
      - 'a4-landscape': Fits image on an A4 Landscape page (842x595 pt) with margin.
      - 'a4-portrait': Fits image on an A4 Portrait page (595x842 pt) with margin.
    """
    if not sorted_records:
        raise ValueError("No images to convert into PDF.")

    output_path = Path(output_pdf_path).resolve()
    
    # If target is a directory or ends in a directory path, create default file inside
    if output_path.is_dir() or str(output_pdf_path).endswith(('/', '\\')):
        output_path = output_path / "Output_Sorted.pdf"
    elif not output_path.suffix or output_path.suffix.lower() != ".pdf":
        output_path = output_path.with_suffix(".pdf")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pil_pages = []

    for r in sorted_records:
        img = Image.open(r["path"])
        
        # Convert RGBA / LA / P to RGB with white background
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            processed_img = background
        else:
            processed_img = img.convert("RGB")

        if page_layout == "native":
            pil_pages.append(processed_img)
        elif page_layout in ("a4-landscape", "a4-portrait"):
            # A4 dimensions in points at 150 DPI or standard 842x595
            is_landscape = (page_layout == "a4-landscape")
            target_w, target_h = (1754, 1240) if is_landscape else (1240, 1754)  # ~150 DPI A4
            
            canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
            # Resize image to fit within target canvas with 5% margin
            margin_w = int(target_w * 0.05)
            margin_h = int(target_h * 0.05)
            max_w = target_w - 2 * margin_w
            max_h = target_h - 2 * margin_h
            
            ratio = min(max_w / processed_img.width, max_h / processed_img.height)
            new_size = (int(processed_img.width * ratio), int(processed_img.height * ratio))
            resized = processed_img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Center on canvas
            paste_x = (target_w - new_size[0]) // 2
            paste_y = (target_h - new_size[1]) // 2
            canvas.paste(resized, (paste_x, paste_y))
            pil_pages.append(canvas)
        else:
            pil_pages.append(processed_img)

    # Save to PDF
    first_page = pil_pages[0]
    first_page.save(
        str(output_path),
        format="PDF",
        save_all=True,
        append_images=pil_pages[1:],
        quality=95,
        optimize=True
    )

    return str(output_path)


def print_summary_table(records: List[Dict[str, Any]]):
    """Prints a structured summary table of sorted pages."""
    print("\n" + "=" * 90)
    print(f"{'Page':<6} | {'Detected Q#':<12} | {'Source Image':<32} | {'Question Snippet':<32}")
    print("-" * 90)
    for idx, r in enumerate(records, 1):
        q_str = f"Q{int(r['qnum'])}" if r['qnum'] is not None and r['qnum'].is_integer() else (f"Q{r['qnum']}" if r['qnum'] is not None else "Unknown")
        fn = r["filename"]
        if len(fn) > 30:
            fn = fn[:27] + "..."
        snippet = r["snippet"].replace("\n", " ")
        if len(snippet) > 32:
            snippet = snippet[:29] + "..."
        print(f"{idx:<6} | {q_str:<12} | {fn:<32} | {snippet:<32}")
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract question numbers from screenshots/images via OCR, sort sequentially, and create a sorted PDF."
    )
    parser.add_argument(
        "-i", "--input-dir",
        default="./Images",
        help="Path to directory containing images (default: ./Images)"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path for generated output PDF (default: <input_dir_name>_Sorted.pdf)"
    )
    parser.add_argument(
        "--layout",
        choices=["native", "a4-landscape", "a4-portrait"],
        default="native",
        help="Page layout format in PDF (default: native)"
    )
    parser.add_argument(
        "--tessdata",
        default=None,
        help="Path to tessdata directory for Tesseract OCR"
    )
    parser.add_argument(
        "--preview",
        "--dry-run",
        action="store_true",
        help="Preview detected question ordering without creating the PDF"
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Reverse sort order (descending)"
    )

    args = parser.parse_args()

    # Determine tessdata directory
    tessdata_dir = args.tessdata or get_tessdata_path()
    if tessdata_dir:
        print(f"[*] Using tessdata at: {tessdata_dir}")

    # Process and sort images
    try:
        sorted_records = collect_and_sort_images(
            input_dir=args.input_dir,
            reverse=args.reverse,
            tessdata_dir=tessdata_dir
        )
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)

    print_summary_table(sorted_records)

    if args.preview:
        print("[*] Preview mode complete. No PDF generated.")
        return

    # Determine output file path
    if args.output:
        raw_output = Path(args.output).resolve()
        if raw_output.is_dir() or str(args.output).endswith(('/', '\\')):
            input_name = Path(args.input_dir).resolve().name
            output_pdf = str(raw_output / f"{input_name}_Sorted.pdf")
        elif not raw_output.suffix or raw_output.suffix.lower() != ".pdf":
            output_pdf = str(raw_output.with_suffix(".pdf"))
        else:
            output_pdf = str(raw_output)
    else:
        parent_dir = Path(args.input_dir).resolve().parent
        input_name = Path(args.input_dir).resolve().name
        output_pdf = str(parent_dir / f"{input_name}_Sorted.pdf")

    print(f"[*] Generating PDF: {output_pdf}")
    result_path = create_pdf(
        sorted_records=sorted_records,
        output_pdf_path=output_pdf,
        page_layout=args.layout
    )
    size_mb = os.path.getsize(result_path) / (1024 * 1024)
    print(f"[✓] Successfully generated sorted PDF with {len(sorted_records)} pages!")
    print(f"[✓] Output file: {result_path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
