"""
Export SYSTEM_FLOWCHART.md Mermaid diagrams to PDF

This script extracts Mermaid diagrams from the flowchart and converts them to PDF.
Uses mermaid-cli (mmdc) which must be installed separately.

Installation:
    npm install -g @mermaid-js/mermaid-cli
    pip install PyPDF2 pillow

Usage:
    python export_diagram_to_pdf.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from io import BytesIO
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def find_mmdc_executable():
    """Find the mmdc executable path"""
    # Try common locations
    possible_paths = [
        'mmdc',
        'mmdc.cmd',
        os.path.join(os.environ.get('APPDATA', ''), 'npm', 'mmdc.cmd'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Roaming', 'npm', 'mmdc.cmd'),
    ]
    
    for mmdc_path in possible_paths:
        try:
            result = subprocess.run([mmdc_path, '--version'], 
                                  capture_output=True, 
                                  text=True,
                                  shell=True)
            if result.returncode == 0:
                print(f"✅ Mermaid CLI found: {result.stdout.strip()}")
                print(f"   Path: {mmdc_path}")
                return mmdc_path
        except:
            continue
    
    print("❌ Mermaid CLI not found!")
    print("\nInstallation steps:")
    print("1. Install Node.js: https://nodejs.org/")
    print("2. Run: npm install -g @mermaid-js/mermaid-cli")
    print("3. Verify: mmdc --version")
    return None

def extract_mermaid_diagrams(markdown_file):
    """Extract all Mermaid diagrams from markdown file"""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all mermaid code blocks
    pattern = r'```mermaid\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    print(f"\n📊 Found {len(matches)} Mermaid diagram(s)")
    return matches

def save_diagram_to_file(diagram_content, output_file):
    """Save Mermaid diagram to .mmd file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(diagram_content)
    print(f"💾 Saved diagram to: {output_file}")

def convert_to_pdf(mmd_file, pdf_file, mmdc_path):
    """Convert .mmd file to PDF using mermaid-cli"""
    try:
        # Use mmdc with PDF output
        cmd = [
            mmdc_path,
            '-i', str(mmd_file),
            '-o', str(pdf_file),
            '-t', 'default',  # theme
            '-b', 'white',    # background color
            '-w', '2400',     # width
            '-H', '2000',     # height - increased to leave room for title
            '--pdfFit'        # Fit content to page
        ]
        
        print(f"🔄 Converting to PDF...")
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(f"✅ PDF created: {pdf_file}")
            return True
        else:
            print(f"❌ Conversion failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        return False

def add_logo_to_pdf(input_pdf, output_pdf, logo_path, title=None, position='bottom-right', logo_size=100):
    """Add logo and optional title to existing PDF with proper margins"""
    try:
        if not Path(logo_path).exists():
            print(f"⚠️  Logo file not found: {logo_path}")
            return False
            
        # Read the existing PDF
        reader = PdfReader(str(input_pdf))
        
        # Get page dimensions
        page = reader.pages[0]
        original_width = float(page.mediabox.width)
        original_height = float(page.mediabox.height)
        
        # Add margins for title and logo
        top_margin = 120 if title else 0
        bottom_margin = 280  # Space for logo
        
        new_width = original_width
        new_height = original_height + top_margin + bottom_margin
        
        # Create new PDF with expanded canvas
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(new_width, new_height))
        
        # Fill white background
        can.setFillColorRGB(1, 1, 1)
        can.rect(0, 0, new_width, new_height, fill=1, stroke=0)
        
        # Draw title if provided
        if title:
            can.setFont("Helvetica-Bold", 36)
            can.setFillColorRGB(0.15, 0.25, 0.45)  # Navy blue color
            title_x = new_width / 2
            title_y = new_height - 70  # 70px from top
            can.drawCentredString(title_x, title_y, title)
        
        # Draw original PDF content in the middle
        can.saveState()
        can.translate(0, bottom_margin)
        can.restoreState()
        
        # Draw the logo in bottom right corner
        margin = 30
        logo_x = new_width - logo_size - margin
        logo_y = margin
        can.drawImage(logo_path, logo_x, logo_y, width=logo_size, height=logo_size, 
                     preserveAspectRatio=True, mask='auto')
        can.save()
        
        # Read overlay
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]
        
        # Get original page and translate it
        original_page = reader.pages[0]
        original_page.mediabox.upper_right = (new_width, new_height)
        original_page.mediabox.lower_left = (0, 0)
        
        # Use cropbox to position original content
        original_page.cropbox.lower_left = (0, bottom_margin)
        original_page.cropbox.upper_right = (original_width, bottom_margin + original_height)
        
        # Merge
        overlay_page.merge_page(original_page)
        
        # Write output
        writer = PdfWriter()
        writer.add_page(overlay_page)
        
        with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"✅ Logo and title added to PDF: {output_pdf}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding logo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main conversion workflow"""
    print("🌊 WaveAlert360 Diagram to PDF Converter")
    print("=" * 60)
    
    # Check for mermaid-cli
    mmdc_path = find_mmdc_executable()
    if not mmdc_path:
        sys.exit(1)
    
    # File paths
    script_dir = Path(__file__).parent
    markdown_file = script_dir / 'SYSTEM_FLOWCHART.md'
    output_dir = script_dir / 'docs'
    output_dir.mkdir(exist_ok=True)
    
    # Logo path
    logo_path = Path(os.environ.get('USERPROFILE', '')) / 'Downloads' / 'wavealert360logo.png'
    
    if not markdown_file.exists():
        print(f"❌ File not found: {markdown_file}")
        sys.exit(1)
    
    print(f"\n📄 Reading: {markdown_file}")
    
    # Extract diagrams
    diagrams = extract_mermaid_diagrams(markdown_file)
    
    if not diagrams:
        print("❌ No Mermaid diagrams found!")
        sys.exit(1)
    
    # Convert each diagram
    for i, diagram in enumerate(diagrams, 1):
        diagram_name = f"system_architecture_{i}" if i == 1 else f"detailed_components_{i}"
        
        # Use specific output filename for first diagram
        if i == 1:
            final_output_name = "WaveAlert360_system_architecture"
        else:
            final_output_name = f"WaveAlert360_detailed_components_{i}"
        
        print(f"\n{'='*60}")
        print(f"Processing Diagram {i}/{len(diagrams)}: {diagram_name}")
        print(f"{'='*60}")
        
        # Save to .mmd file
        mmd_file = output_dir / f"{diagram_name}.mmd"
        save_diagram_to_file(diagram, mmd_file)
        
        # Convert to PDF (temporary file)
        temp_pdf_file = output_dir / f"{diagram_name}_temp.pdf"
        final_pdf_file = output_dir / f"{final_output_name}.pdf"
        
        if convert_to_pdf(mmd_file, temp_pdf_file, mmdc_path):
            # Add logo and title to the PDF
            if logo_path.exists():
                title = "WaveAlert360 System Architecture" if i == 1 else "WaveAlert360 Detailed Components"
                add_logo_to_pdf(temp_pdf_file, final_pdf_file, str(logo_path), 
                              title=title, position='bottom-right', logo_size=240)
                # Remove temporary PDF
                temp_pdf_file.unlink()
            else:
                print(f"⚠️  Logo not found at {logo_path}, skipping logo...")
                temp_pdf_file.rename(final_pdf_file)
        
        # Optionally clean up .mmd file
        # mmd_file.unlink()
    
    # Clean up old files
    old_file = output_dir / "WaveAlert360_system_architecture_1.pdf"
    if old_file.exists():
        old_file.unlink()
        print(f"\n🗑️  Deleted old file: {old_file.name}")
    
    print("\n" + "=" * 60)
    print("✅ Export Complete!")
    print(f"📁 Output directory: {output_dir}")
    print("\nGenerated files:")
    for pdf in output_dir.glob("WaveAlert360_*.pdf"):
        print(f"  - {pdf.name}")
    total_size = sum(f.stat().st_size for f in output_dir.glob('WaveAlert360_*.pdf'))
    if total_size > 0:
        print(f"\nTotal size: {total_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
