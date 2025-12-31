# common/cad_rules.py
import pandas as pd
import re
import os
from config import Config

CAD_MAIN_CODES = set()
CAD_UNSTABLE_CODES = set()
COMPLEX_SECONDARY_CODES = set()

def load_cad_rules():
    global CAD_MAIN_CODES, CAD_UNSTABLE_CODES, COMPLEX_SECONDARY_CODES
    if not os.path.exists(Config.CAD_RULE_PATH):
        raise FileNotFoundError(f"找不到 CAD_rule.csv：{Config.CAD_RULE_PATH}")
    
    df = pd.read_csv(Config.CAD_RULE_PATH, encoding='utf-8')
    print("實際欄位名稱：", list(df.columns))
    
    for _, row in df.iterrows():
        # 動態取欄位
        cols = df.columns
        category = str(row[cols[0]]).strip().lower()
        condition = str(row[cols[1]]).strip().lower()
        codes_str = str(row[cols[2]]).strip()
        
        if codes_str == 'nan' or not codes_str:
            continue
        
        codes = [code.strip() for code in codes_str.split(',') if code.strip()]
        
        if category == 'main':
            CAD_MAIN_CODES.update(codes)
            if 'unstable' in condition or 'refractory' in condition:
                CAD_UNSTABLE_CODES.update(codes)
        elif category == 'complex':
            COMPLEX_SECONDARY_CODES.update(codes)
    
    print("CAD 主診斷碼（所有）：", sorted(CAD_MAIN_CODES))
    print("CAD 不穩定型碼：", sorted(CAD_UNSTABLE_CODES))
    print("複雜次診斷碼：", sorted(COMPLEX_SECONDARY_CODES))

load_cad_rules()