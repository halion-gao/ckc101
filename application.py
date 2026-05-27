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

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8080)
