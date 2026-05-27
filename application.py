import os
# pyrefly: ignore [missing-import]
from flask import Flask, render_template

application = Flask(__name__)

@application.route('/')
def home():
    # 這裡定義你的 Google 文件 ID
    google_doc_id = "1oupJh4l6Dlrun8gNbK0H83in7Kn6lhAnfxIMITR-PxU" 
    return render_template('blog.html', doc_id=google_doc_id)

@application.route('/aws-guide')
def aws_guide():
    # 這是你提供的文件 ID
    doc_id = "1oupJh4l6Dlrun8gNbK0H83in7Kn6lhAnfxIMITR-PxU"
    return render_template('post.html', doc_id=doc_id)

@application.route('/github')
def github_preview():
    # Read README.md content to render it in front-end
    readme_content = ""
    if os.path.exists("README.md"):
        try:
            with open("README.md", "r", encoding="utf-8") as f:
                readme_content = f.read()
        except Exception:
            readme_content = "# Error reading README.md"

    # Build the file list
    file_list = []
    for root, dirs, files in os.walk('.'):
        # Exclude directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', '.venv', '__pycache__', 'sre_app_stderr.log')]
        for file in files:
            if not file.startswith('.'):
                file_path = os.path.relpath(os.path.join(root, file), '.')
                file_list.append(file_path)

    # Sort the files alphabetically
    file_list.sort()
    
    return render_template('github.html', files=file_list, readme=readme_content)

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8080)
