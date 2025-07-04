# Resume & Cover Letter Generator with LLM

This application allows users to generate professional resumes and cover letters using a locally-running Large Language Model (LLM) through Ollama. Simply enter your personal information, and the app creates well-formatted PDF documents ready for job applications.

## Features
- **AI-powered document generation** using your local LLMs through Ollama
- **Professionally formatted PDF output** with proper styling and structure
- **User-friendly interface** built with Streamlit
- **Works offline** once set up, as it runs entirely on your machine
- **Supports multiple LLM models** that are available in Ollama

## Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running with at least one model
- Recommended models: Gemma, Llama3, or any model that performs well with text generation

## Installation

1. **Clone the repository**
   ```
   git clone https://github.com/hari7261/Resume-CoverLetterGenerator-LLM.git
   cd Resume-CoverLetterGenerator-LLM
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Install and run Ollama**
   - Download from [ollama.ai](https://ollama.ai/)
   - Follow installation instructions
   - Run `ollama serve` to start the service
   - Pull a model, e.g., `ollama pull gemma3`

## Usage

1. **Start the application**
   ```
   streamlit run app.py
   ```

2. **Fill in your information**
   - Enter your full name
   - Select or type your target job role
   - Add your work experience
   - List your key skills (comma-separated)

3. **Select a model**
   - Choose from available Ollama models
   - Or enter a model name manually

4. **Generate and download**
   - Click "Generate Documents"
   - Download your resume and cover letter as PDFs

## Application Structure

- `app.py` - Main Streamlit application file
- `DejaVuSansCondensed.ttf` - Font file for PDF generation
- `requirements.txt` - Python dependencies
- `docs/` - Documentation assets

## How It Works

1. **Data Collection**: User inputs their information through a Streamlit interface
2. **LLM Generation**: Data is sent to a locally running LLM via Ollama
3. **Document Processing**: The application splits and formats the LLM response
4. **PDF Creation**: Professional PDFs are created with FPDF
5. **Download**: Documents are made available for download

## Customization

You can customize the document generation by:

- Modifying the prompt in the `app.py` file
- Changing the PDF styling in the `create_pdf` function
- Adding additional input fields to collect more user information

## Troubleshooting

- **"Could not connect to Ollama"**: Ensure Ollama is running with `ollama serve`
- **No models available**: Make sure you've pulled at least one model with `ollama pull <model-name>`
- **PDF generation errors**: Check that the font file is accessible

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the web interface framework
- [FPDF](https://pyfpdf.github.io/fpdf2/) for PDF generation
- [Ollama](https://ollama.ai/) for local LLM integration

---

Created by [Hariom Kumar](https://github.com/hari7261)
