"""
Script to generate PDF test files from text contracts for testing the contract processing API
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

def text_to_pdf(text_file_path, pdf_file_path):
    """Convert a text file to PDF"""
    
    # Read the text file
    with open(text_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_file_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor='black'
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.spaceAfter = 12
    
    # Split content into lines and create paragraphs
    story = []
    lines = content.split('\n')
    
    # First line as title if it looks like a title
    if lines and lines[0].isupper() and len(lines[0]) < 50:
        story.append(Paragraph(lines[0], title_style))
        story.append(Spacer(1, 20))
        content_lines = lines[1:]
    else:
        content_lines = lines
    
    # Process remaining content
    current_paragraph = []
    
    for line in content_lines:
        line = line.strip()
        if line == '':
            if current_paragraph:
                story.append(Paragraph('<br/>'.join(current_paragraph), normal_style))
                current_paragraph = []
                story.append(Spacer(1, 12))
        else:
            current_paragraph.append(line)
    
    # Add any remaining content
    if current_paragraph:
        story.append(Paragraph('<br/>'.join(current_paragraph), normal_style))
    
    # Build PDF
    doc.build(story)
    print(f"Generated PDF: {pdf_file_path}")

def main():
    """Generate all test PDF files"""
    
    # Check if reportlab is available
    try:
        import reportlab
    except ImportError:
        print("Error: reportlab is required. Install with: pip install reportlab")
        return
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Files to convert
    text_files = [
        'sample_service_contract.txt',
        'sample_rental_lease.txt', 
        'sample_consulting_agreement.txt',
        'sample_contract.txt'  # Existing file
    ]
    
    print("Generating PDF test files...")
    
    for text_file in text_files:
        text_path = os.path.join(base_dir, text_file)
        if os.path.exists(text_path):
            pdf_file = text_file.replace('.txt', '.pdf')
            pdf_path = os.path.join(base_dir, pdf_file)
            
            try:
                text_to_pdf(text_path, pdf_path)
            except Exception as e:
                print(f"Error generating {pdf_file}: {e}")
        else:
            print(f"Warning: {text_file} not found")
    
    print("\nPDF generation completed!")
    print("\nGenerated files:")
    for file in os.listdir(base_dir):
        if file.endswith('.pdf'):
            print(f"  - {file}")

if __name__ == "__main__":
    main()