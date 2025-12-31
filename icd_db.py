# common/icd_db.py
import pandas as pd
import os
from config import Config

icd_dict = {}

def load_icd_db():
    global icd_dict
    if not os.path.exists(Config.ICD_CSV_PATH):
        raise FileNotFoundError(f"找不到 ICD_code.csv：{Config.ICD_CSV_PATH}")
    
    df = pd.read_csv(Config.ICD_CSV_PATH, encoding='utf-8')
    for _, row in df.iterrows():
        code = str(row['疾病代碼']).strip()
        if code != 'nan':
            icd_dict[code] = {
                'english': str(row.get('CM 英文名稱(2023)', '')),
                'chinese': str(row.get('CM 中文名稱(2023)', ''))
            }
    print(f"ICD DB 載入完成，共 {len(icd_dict)} 筆")

load_icd_db()  # 啟動時自動載入