import streamlit as st
import ollama
from fpdf import FPDF
import re
import os

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

# Create a function to generate PDFs with proper formatting
def create_pdf(content, filename, title):
    pdf = FPDF()
    # Add a Unicode font
    pdf.add_font('DejaVu', '', os.path.join(os.path.dirname(__file__), 'DejaVuSansCondensed.ttf'), uni=True)
    pdf.set_font('DejaVu', '', 12)
    
    pdf.add_page()
    # Add title
    pdf.set_font('DejaVu', '', 16)
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.ln(5)
    
    # Reset to normal text size
    pdf.set_font('DejaVu', '', 12)
    
    # Add content with proper line breaks
    for line in content.split('\n'):
        if line.strip():
            pdf.multi_cell(0, 8, line)
        else:
            pdf.ln(4)
    
    pdf.output(filename)
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
                
                # Check if DejaVu font exists, if not, download it
                font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSansCondensed.ttf')
                if not os.path.exists(font_path):
                    st.warning("Unicode font not found. Using default font which may not display all characters correctly.")
                
                # Create PDFs
                resume_file = create_pdf(resume_text, "resume.pdf", f"{name} - Resume")
                cover_letter_file = create_pdf(cover_letter_text, "cover_letter.pdf", f"{name} - Cover Letter")
                
                # Display download buttons
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("Download Resume", open("resume.pdf", "rb"), file_name=f"{name}_Resume.pdf")
                with col2:
                    st.download_button("Download Cover Letter", open("cover_letter.pdf", "rb"), file_name=f"{name}_CoverLetter.pdf")
                
            except Exception as e:
                st.error(f"Error generating content: {str(e)}")
                st.info("Common solutions:\n- Install a Unicode font\n- Check if Ollama service is running\n- Try a different model")