import streamlit as st
import ollama
from fpdf import FPDF
import re
import os
import time
import requests
import io
from PIL import Image
from contextlib import contextmanager
from urllib.request import urlopen

# Add a function to clean markdown formatting
def clean_markdown(text):
    # Remove headers
    text = re.sub(r'#+\s+', '', text)
    # Remove bold/italic markers
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'\*|_', '', text)
    # Remove bullet points
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
    # Remove backticks
    text = re.sub(r'`', '', text)
    # Replace fancy quotes and dashes with simple ones
    text = text.replace('–', '-').replace('"', '"').replace('"', '"')
    return text

# Check if font exists and download it if needed
def ensure_font_available():
    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSansCondensed.ttf')
    if not os.path.exists(font_path):
        try:
            st.info("Downloading required font for PDF generation...")
            # URL to DejaVu Sans Condensed TTF
            font_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansCondensed.ttf"
            response = requests.get(font_url)
            if response.status_code == 200:
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                st.success("Font downloaded successfully!")
                return True
            else:
                st.warning("Could not download font. Using built-in fonts instead.")
                return False
        except Exception as e:
            st.warning(f"Error downloading font: {str(e)}. Using built-in fonts instead.")
            return False
    return True

# Helper for safely calling Ollama
@contextmanager
def safe_ollama_call():
    try:
        yield
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to Ollama. Please make sure Ollama is running.")
        st.info("To start Ollama, run 'ollama serve' in a terminal.")
        st.stop()
    except Exception as e:
        st.error(f"Ollama error: {str(e)}")
        st.info("Please check if Ollama is running and the model is available.")
        st.stop()

# Add a function to split resume and cover letter
def split_documents(text):
    # Look for clear dividers between resume and cover letter
    parts = re.split(r'(?i)#+\s*(cover\s*letter|resume)', text)
    
    if len(parts) >= 3:
        # If we found proper headers
        resume = parts[0]
        if "cover" in parts[1].lower():
            cover_letter = parts[2]
        else:
            resume = parts[2]
            cover_letter = parts[0]
    else:
        # Try to split based on length and structure
        lines = text.split('\n')
        split_point = len(lines) // 2
        
        # Look for a better split point
        for i in range(len(lines)):
            if re.match(r'(?i).*cover\s*letter.*', lines[i]):
                split_point = i
                break
        
        resume = '\n'.join(lines[:split_point])
        cover_letter = '\n'.join(lines[split_point:])
    
    return clean_markdown(resume), clean_markdown(cover_letter)

# Improved PDF generation with better styling and error handling
def create_pdf(content, filename, title, document_type="resume"):
    try:
        pdf = FPDF()
        
        # Try to use DejaVu font, fall back to built-in if not available
        font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSansCondensed.ttf')
        
        if os.path.exists(font_path):
            pdf.add_font('DejaVu', '', font_path, uni=True)
            pdf.add_font('DejaVu', 'B', font_path, uni=True)
            font_family = 'DejaVu'
        else:
            # Fall back to built-in font
            font_family = 'Arial'
        
        # Page setup
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Add title with better styling
        pdf.set_font(font_family, 'B', 18)
        pdf.set_text_color(44, 62, 80)  # Dark blue-gray
        pdf.cell(0, 15, title, 0, 1, 'C')
        pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
        pdf.ln(10)
        
        # Process content with better formatting
        pdf.set_font(font_family, '', 11)
        pdf.set_text_color(0, 0, 0)
        
        # For resume, format sections differently
        if document_type == "resume":
            sections = content.split('\n\n')
            for section in sections:
                lines = section.split('\n')
                if len(lines) > 0 and lines[0].strip():
                    # Check if this looks like a section header
                    if len(lines) > 1 and len(lines[0]) < 30 and not lines[0].startswith('•'):
                        pdf.set_font(font_family, 'B', 14)
                        pdf.set_text_color(44, 62, 80)
                        pdf.cell(0, 10, lines[0], 0, 1, 'L')
                        pdf.set_font(font_family, '', 11)
                        pdf.set_text_color(0, 0, 0)
                        
                        # Process remaining lines
                        for line in lines[1:]:
                            if line.startswith('•'):
                                pdf.cell(5, 6, '', 0, 0)
                                pdf.multi_cell(0, 6, line)
                            else:
                                pdf.multi_cell(0, 6, line)
                    else:
                        for line in lines:
                            pdf.multi_cell(0, 6, line)
                pdf.ln(4)
        else:
            # Cover letter format
            for line in content.split('\n'):
                if line.strip():
                    if line.strip() == title.split(' - ')[0]:  # If line is the name
                        pdf.set_font(font_family, 'B', 12)
                        pdf.multi_cell(0, 8, line)
                        pdf.set_font(font_family, '', 11)
                    elif line.startswith('Dear') or line.startswith('Sincerely'):
                        pdf.set_font(font_family, 'B', 11)
                        pdf.multi_cell(0, 8, line)
                        pdf.set_font(font_family, '', 11)
                    else:
                        pdf.multi_cell(0, 6, line)
                else:
                    pdf.ln(4)
        
        # Add footer
        pdf.set_y(-15)
        pdf.set_font(font_family, 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 10, f'Generated on {time.strftime("%B %d, %Y")}', 0, 0, 'C')
        
        # Save file
        pdf.output(filename)
        return filename
        
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        # Create a very simple backup PDF as fallback
        try:
            simple_pdf = FPDF()
            simple_pdf.add_page()
            simple_pdf.set_font('Arial', '', 12)
            simple_pdf.cell(0, 10, title, 0, 1, 'C')
            simple_pdf.multi_cell(0, 10, content)
            simple_pdf.output(filename)
            return filename
        except:
            raise Exception("Could not create PDF with any method")

# Check available models with better error handling
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_available_models():
    with safe_ollama_call():
        try:
            models = ollama.list()
            if 'models' in models and isinstance(models['models'], list):
                return [model.get('name', model.get('model', '')) for model in models['models']]
            else:
                st.warning("Unexpected Ollama API response structure. Using manual model entry instead.")
                return []
        except Exception as e:
            st.warning(f"Could not retrieve models list: {str(e)}")
            return []

# Page title
st.title("Document Generator")

# User Inputs
name = st.text_input("Full Name")
job_role = st.selectbox("Target Role", ["Software Engineer", "Data Scientist", "Marketing Manager"])
experience = st.text_area("Work Experience")
skills = st.text_input("Key Skills (comma-separated)")

# Model Selection
available_models = get_available_models()
use_manual_model = st.checkbox("Enter model name manually", value=len(available_models) == 0)

if use_manual_model:
    selected_model = st.text_input("Model name", value="gemma3")
elif available_models:
    selected_model = st.selectbox("Select Model", available_models)
else:
    st.error("No Ollama models found and manual entry disabled. Please check your Ollama installation.")
    st.stop()

# Add information about Ollama status
try:
    with st.sidebar:
        st.write("## Ollama Status")
        with safe_ollama_call():
            ollama_status = "✅ Connected"
            st.success(ollama_status)
except:
    with st.sidebar:
        st.write("## Ollama Status")
        st.error("❌ Not connected")
        st.info("Make sure Ollama is running (`ollama serve`)")

# Ensure font is available
ensure_font_available()

# Generate Resume/Cover Letter using LLM
if st.button("Generate Documents", type="primary"):
    if not all([name, experience, skills]):
        st.error("Please fill in all required fields.")
    else:
        # Create progress bar
        progress_text = "Generating documents..."
        progress_bar = st.progress(0, text=progress_text)
        
        # Setup the generation process
        try:
            # Update progress
            progress_bar.progress(10, text="Setting up prompt...")
            
            # LLM Prompt with improved instructions
            prompt = f"""
            Create a professional resume and cover letter for {name} applying as {job_role}.
            
            Experience: {experience}
            Skills: {skills}
            
            Format both documents professionally as follows:
            
            RESUME:
            - Start with the name and job role
            - Include a professional summary
            - Detail work experience
            - List key skills
            - Add education information
            
            COVER LETTER:
            - Use a standard business letter format
            - Address to "Dear Hiring Manager,"
            - Express interest in the {job_role} position
            - Highlight relevant experience and skills
            - Close with "Sincerely," and name
            
            Clearly separate the two documents with headers (RESUME and COVER LETTER).
            Do NOT include any markdown formatting symbols in the final output.
            Keep content professional, concise and well-structured.
            """
            
            # Update progress
            progress_bar.progress(20, text="Connecting to Ollama...")
            
            # Get LLM response with enhanced error handling
            with safe_ollama_call():
                progress_bar.progress(30, text="Generating content with LLM...")
                response = ollama.generate(model=selected_model, prompt=prompt)
                progress_bar.progress(60, text="Processing generated content...")
            
            # Display the raw response
            with st.expander("Generated Content"):
                st.markdown(response["response"])
            
            # Split and clean the response
            progress_bar.progress(70, text="Formatting documents...")
            resume_text, cover_letter_text = split_documents(response["response"])
            
            # Update progress
            progress_bar.progress(80, text="Creating PDFs...")
            
            # Create PDFs with improved styling
            resume_file = create_pdf(resume_text, "resume.pdf", f"{name} - Resume", document_type="resume")
            cover_letter_file = create_pdf(cover_letter_text, "cover_letter.pdf", f"{name} - Cover Letter", document_type="cover_letter")
            
            # Update progress
            progress_bar.progress(100, text="Documents ready!")
            
            # Display success message
            st.success("✅ Documents generated successfully!")
            
            # Display download buttons with improved UI
            st.write("### Download Your Documents")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📄 Download Resume", 
                    open("resume.pdf", "rb"), 
                    file_name=f"{name}_Resume.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    "📝 Download Cover Letter", 
                    open("cover_letter.pdf", "rb"), 
                    file_name=f"{name}_CoverLetter.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"Error generating content: {str(e)}")
            st.info("""Common solutions:
            1. Check if Ollama service is running (`ollama serve` in terminal)
            2. Try a different model
            3. Restart the application""")
            
            # Log error for debugging
            st.warning(f"Detailed error: {str(e)}", icon="⚠️")