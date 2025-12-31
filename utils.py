# common/utils.py
import re
from .icd_db import icd_dict
import docx
import fitz

# 輔助函數：替換單行中的所有 ICD 碼為中英文格式
def replace_icd_codes_in_line(line):
    def replace_match(match):
        raw_code = match.group(1).upper()
        code_nodot = raw_code.replace('.', '')
        
        entry = icd_dict.get(code_nodot, {})
        english = entry.get('english', '').strip()
        chinese = entry.get('chinese', '').strip()
        
        display_code = code_nodot[:3] + '.' + code_nodot[3:] if len(code_nodot) > 3 else code_nodot
        
        if english and english != 'nan':
            display_text = f"{display_code} - {english}"
        else:
            display_text = f"{display_code}"
        
        if chinese and chinese != 'nan':
            display_text += f" ({chinese})"
        
        return display_text
    
    return re.sub(r"([A-Z]\d{1,6}(?:\.\d{1,3})?)", replace_match, line, flags=re.IGNORECASE)

# 後端處理函數：修正碼 + 替換官方名稱
def post_process_icd_with_cad(text):
    lines = text.strip().split('\n')
    result = []
    in_cad_section = False
    
    for line in lines:
        original_line = line.strip()
        if not original_line:
            result.append("")
            continue
        
        if "【CAD 判斷結果】" in original_line:
            in_cad_section = True
            result.append("========================================================================================================")
            result.append("【CAD 判斷結果】")
            result.append("========================================================================================================")
            result.append(original_line.replace("【CAD 判斷結果】", "").strip())
            continue
        
        if in_cad_section:
            result.append(replace_icd_codes_in_line(original_line))
        
        elif "【一般 ICD 推薦】" in original_line:
            result.append("")
            result.append("========================================================================================================")
            result.append("一般 ICD-10 診斷推薦（含中英文名稱）")
            result.append("========================================================================================================")
        
        else:
            result.append(replace_icd_codes_in_line(original_line))
    
    return "\n".join(result)

# 讀取 Word
def read_word_file(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

# 讀取 PDF
def read_pdf_file(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text("text").strip() + "\n"
    doc.close()
    return text