# app.py
from flask import Flask, render_template
from tasks.icd_recommend import icd_bp
from tasks.generate_summary import summary_bp  

app = Flask(__name__)
from config import Config
app.secret_key = Config.SECRET_KEY

# 註冊所有 blueprint
app.register_blueprint(icd_bp)           # ICD 任務
app.register_blueprint(summary_bp)       # <-- 關鍵：加這行註冊 Summary 任務

@app.route('/')
def index():
    return render_template('index_integrate.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
