# config.py
import os

class Config:
    SECRET_KEY = 'fixed_super_secret_key_2025_do_not_change'
    
    # Azure OpenAI 設定
    AZURE_API_KEY = ""
    AZURE_ENDPOINT = ""
    API_VERSION = ""
    DEPLOYMENT = "gpt-4o"
    
    # 檔案路徑
    ICD_CSV_PATH = "ICD_code.csv"
    CAD_RULE_PATH = "CAD_rule.csv"