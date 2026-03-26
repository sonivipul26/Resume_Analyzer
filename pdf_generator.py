import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

def _create_pdf(pdf_data, html_string):
    """Utility to generate PDF from string."""
    with open(pdf_data, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(
            html_string, 
            dest=result_file
        )
    return pisa_status.err

def generate_pdf_from_json(resume_data: dict, output_path: str = "optimized_resume.pdf", template_name: str = "single_column.html") -> str:
    """
    Renders an HTML template with the resume_data dictionary and converts it to a PDF file.
    Returns the absolute path to the generated PDF.
    """
    try:
        # Load Jinja template
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template(template_name)

        # Render HTML string
        html_out = template.render(**resume_data)

        # Generate PDF
        error = _create_pdf(output_path, html_out)
        
        if error:
            print("Error generating PDF:", error)
        
        return os.path.abspath(output_path)
    except Exception as e:
        print(f"Exception during PDF generation: {e}")
        return ""
