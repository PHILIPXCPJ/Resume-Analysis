from flask import Flask, render_template, request, flash
from parser import ResumeParser
from file_parser import FileParser
import os

app = Flask(__name__)
app.secret_key = 'dev-key-123'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Supported file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'rtf'}

parser = ResumeParser()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file selected')
            return render_template('upload.html')
        
        file = request.files['resume']
        if file.filename == '':
            flash('No file selected')
            return render_template('upload.html')
        
        if not allowed_file(file.filename):
            flash('File type not supported. Please upload PDF, DOCX, DOC, or TXT.')
            return render_template('upload.html')
        
        try:
            # Save the file temporarily
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            
            # Process the file
            text = FileParser.extract_text(filename)
            results = parser.parse(text)
            
            # Delete the temporary file
            os.remove(filename)
            
            return render_template('results.html', results=results)
        
        except Exception as e:
            flash(f'Error: {str(e)}')
            return render_template('upload.html')
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)