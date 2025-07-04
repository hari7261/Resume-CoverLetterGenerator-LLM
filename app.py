import streamlit as st
import ollama
import re
import os
# Replace FPDF with ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

# Create a function to generate PDFs with proper formatting using ReportLab
def create_pdf(content, filename, title):
    # Setup document with letter size page
    doc = SimpleDocTemplate(filename, pagesize=letter)
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    normal_style.leading = 14  # Line spacing
    
    # Create elements list for document
    elements = []
    
    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))
    
    # Process content paragraphs
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if not para.strip():
            continue
            
        # Handle bullet points
        lines = para.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('• ') or line.startswith('* '):
                    # Create bullet point paragraph with indentation
                    bullet_style = ParagraphStyle(
                        'bullet',
                        parent=normal_style,
                        leftIndent=20,
                        firstLineIndent=-15
                    )
                    elements.append(Paragraph("• " + line[2:], bullet_style))
                else:
                    elements.append(Paragraph(line, normal_style))
        
        # Add space between paragraphs
        elements.append(Spacer(1, 10))
    
    # Build the document
    doc.build(elements)
    return filename

# Check available models
@st.cache_data
def get_available_models():
    try:
        models = ollama.list()
        if 'models' in models:
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

# Generate Resume/Cover Letter
if st.button("Generate Documents"):
    if not all([name, experience, skills]):
        st.error("Please fill in all required fields.")
    else:
        with st.spinner("Creating..."):
            # LLM Prompt with better formatting instructions
            prompt = f"""
            Create a professional resume and cover letter for {name} applying as {job_role}.
            
            Experience: {experience}
            Skills: {skills}
            
            Format both documents professionally. First create the RESUME, then create the COVER LETTER.
            Clearly separate the two documents with headers.
            Do NOT include any markdown formatting symbols in the final output.
            """
            
            try:
                # Get LLM response
                response = ollama.generate(model=selected_model, prompt=prompt)
                
                # Display the raw response
                with st.expander("Generated Content"):
                    st.markdown(response["response"])
                
                # Split and clean the response
                resume_text, cover_letter_text = split_documents(response["response"])
                
                # Create PDFs with ReportLab
                try:
                    resume_file = create_pdf(resume_text, "resume.pdf", f"{name} - Resume")
                    cover_letter_file = create_pdf(cover_letter_text, "cover_letter.pdf", f"{name} - Cover Letter")
                    
                    # Display download buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        with open(resume_file, "rb") as f:
                            st.download_button("Download Resume", f, file_name=f"{name}_Resume.pdf")
                    with col2:
                        with open(cover_letter_file, "rb") as f:
                            st.download_button("Download Cover Letter", f, file_name=f"{name}_CoverLetter.pdf")
                
                except Exception as pdf_error:
                    st.error(f"Error creating PDF: {str(pdf_error)}")
                    st.info("Displaying text version instead:")
                    
                    # Show text versions if PDF creation fails
                    with st.expander("Resume (Text Version)"):
                        st.text(resume_text)
                    with st.expander("Cover Letter (Text Version)"):
                        st.text(cover_letter_text)
                
            except Exception as e:
                st.error(f"Error generating content: {str(e)}")
                st.info("Common solutions:\n- Check if Ollama service is running\n- Try a different model")