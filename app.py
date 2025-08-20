# app.py
from flask import Flask, render_template, request, jsonify
import os
import re
import PyPDF2
import docx2txt
import nltk
import spacy
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Define section keywords
SECTION_KEYWORDS = {
    'contact': ['phone', 'email', 'address', 'linkedin', 'github', 'contact'],
    'education': ['education', 'university', 'college', 'degree', 'bachelor', 'master', 'phd', 'diploma', 'gpa', 'academic'],
    'experience': ['experience', 'work', 'employment', 'job', 'position', 'role', 'career', 'company', 'organization'],
    'skills': ['skills', 'technologies', 'tools', 'programming', 'languages', 'competencies', 'technical', 'proficient'],
    'projects': ['projects', 'portfolio', 'research', 'developed', 'implemented', 'built', 'created'],
    'achievements': ['achievements', 'awards', 'honors', 'recognition', 'accomplishments', 'certifications'],
    'summary': ['summary', 'objective', 'profile', 'about', 'overview', 'professional summary']
}

# Required elements for a good resume
REQUIRED_ELEMENTS = {
    'contact': 'Contact information',
    'education': 'Educational background',
    'experience': 'Work experience',
    'skills': 'Skills and competencies',
    'achievements': 'Achievements or certifications',
    'summary': 'Professional summary'
}

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
    return text.strip()

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file"""
    try:
        text = docx2txt.process(docx_path)
        return text.strip()
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        return ""

def extract_text(file_path):
    """Extract text based on file extension"""
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    else:
        return ""

def preprocess_text(text):
    """Preprocess the extracted text"""
    # Convert to lowercase
    text = text.lower()
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    return text

def identify_sections(text):
    """Identify different sections in the resume"""
    found_sections = {}
    preprocessed_text = preprocess_text(text)
    
    for section, keywords in SECTION_KEYWORDS.items():
        section_score = 0
        for keyword in keywords:
            if keyword in preprocessed_text:
                section_score += preprocessed_text.count(keyword)
        
        found_sections[section] = section_score > 0
    
    return found_sections

def extract_skills(text):
    """Extract potential skills from the resume text"""
    doc = nlp(text.lower())
    
    # Common skill-related keywords
    skill_patterns = [
        'python', 'java', 'javascript', 'c++', 'c#', 'react', 'angular', 'vue', 
        'node', 'html', 'css', 'sql', 'nosql', 'mongodb', 'mysql', 'postgresql',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'cloud', 'machine learning',
        'data science', 'artificial intelligence', 'ai', 'ml', 'deep learning',
        'natural language processing', 'nlp', 'computer vision', 'data analysis',
        'data visualization', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
        'pandas', 'numpy', 'project management', 'agile', 'scrum', 'leadership',
        'communication', 'teamwork', 'problem solving', 'critical thinking',
        'presentation', 'excel', 'office', 'photoshop', 'illustrator', 'design',
        'ui', 'ux', 'frontend', 'backend', 'fullstack', 'mobile', 'android', 'ios',
        'swift', 'kotlin', 'flutter', 'react native', 'git', 'github', 'ci/cd'
    ]
    
    found_skills = []
    for skill in skill_patterns:
        if skill in text.lower():
            found_skills.append(skill)
    
    # Extract noun phrases as potential skills
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 3:  # Limit to phrases with max 3 words
            # Check if not a stopword and not already found
            if chunk.text.lower() not in found_skills and chunk.root.text not in stopwords.words('english'):
                found_skills.append(chunk.text.lower())
    
    # Remove duplicates and clean up
    cleaned_skills = []
    for skill in found_skills:
        skill = skill.strip()
        if skill and len(skill) > 2 and skill not in cleaned_skills:
            cleaned_skills.append(skill)
    
    return cleaned_skills[:20]  # Return top 20 skills

def analyze_resume(text):
    """Analyze the resume and provide feedback"""
    # Identify sections
    found_sections = identify_sections(text)
    
    # Extract potential skills
    skills = extract_skills(text)
    
    # Check what's missing
    missing_sections = []
    for section, name in REQUIRED_ELEMENTS.items():
        if not found_sections.get(section, False):
            missing_sections.append(name)
    
    # Get word count as a basic density metric
    word_count = len(text.split())
    
    # Check content density
    is_too_short = word_count < 300
    is_too_long = word_count > 1000
    
    # Prepare analysis results
    analysis = {
        'sections_found': {section: found for section, found in found_sections.items()},
        'missing_sections': missing_sections,
        'skills_found': skills,
        'word_count': word_count,
        'is_too_short': is_too_short,
        'is_too_long': is_too_long
    }
    
    # Generate recommendations
    recommendations = []
    
    # Add section-specific recommendations
    for section, name in REQUIRED_ELEMENTS.items():
        if not found_sections.get(section, False):
            recommendations.append(f"Add a {name.lower()} section to your resume.")
    
    # Add skill recommendations
    if len(skills) < 5:
        recommendations.append("Include more specific skills related to your field.")
    
    # Add length recommendations
    if is_too_short:
        recommendations.append("Your resume is quite short. Consider adding more details about your experience and skills.")
    if is_too_long:
        recommendations.append("Your resume is quite long. Consider condensing it to highlight your most relevant experiences.")
    
    # Add some general recommendations
    if not found_sections.get('achievements', False):
        recommendations.append("Including measurable achievements can make your resume stand out.")
    
    analysis['recommendations'] = recommendations
    
    return analysis

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.pdf', '.docx']:
        return jsonify({'error': 'Only PDF and DOCX files are supported'}), 400
    
    # Save the file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    # Extract text from the file
    text = extract_text(file_path)
    
    # If no text was extracted
    if not text:
        os.remove(file_path)
        return jsonify({'error': 'Could not extract text from the file'}), 400
    
    # Analyze the resume
    analysis = analyze_resume(text)
    
    # Clean up the uploaded file
    os.remove(file_path)
    
    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True)