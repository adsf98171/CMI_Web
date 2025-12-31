# tasks/icd_recommend.py
from flask import Blueprint, request, jsonify
from common.azure_client import get_client_and_deployment
from common.cad_rules import CAD_MAIN_CODES, CAD_UNSTABLE_CODES, COMPLEX_SECONDARY_CODES
from common.utils import post_process_icd_with_cad
import os
import json

icd_bp = Blueprint('icd', __name__)

CAD_ANALYSIS_PROMPT = f"""
你是一位心臟內科主治醫師，正在協助醫院內部 DRG 品質審查計畫。
你的任務是從病歷中重建臨床事件，並嚴謹判斷本次住院是否以冠狀動脈疾病（CAD）為主診斷，以及是否符合複雜型標準。

【重要原則】（嚴格遵守）
- 不要完全依賴出院診斷或醫師寫的診斷名稱（可能遺漏或不精確）
- 必須從臨床事件（症狀、檢查、處置）重建真實病情
- 只有「明確事件支持」的診斷才可認定

【CAD 判斷規則】

[step1]重現主要臨床事件

從住院病歷中，識別出：

急性缺血性心臟事件

急性器官功能障礙事件

顯示臨床嚴重程度的主要介入措施。請專注於事件，而非診斷標籤。事件範例：

伴隨缺血性心電圖改變的急性胸痛

心肌酵素升高伴隨動態變化

緊急冠狀動脈造影或急診經皮冠狀動脈介入治療 (PCI)

需要靜脈利尿劑或吸氧氣的肺水腫

使用正性肌力藥物、主動脈內球囊反搏 (IABP)、呼吸器支持 

[step2]推斷臨床等效診斷 

急性心肌梗塞 (AMI)

嚴重併發症（例如，急性心臟衰竭，休克、呼吸衰竭）

併發症（例如，需要治療的心律不整、急性腎損傷） 對於每個推論的診斷，請具體說明：

明確記錄/事件重建

支持性證據（引用） 

[step3]生成建議 DRG 組 (參考:{', '.join(sorted(CAD_MAIN_CODES))}) 

使用以下邏輯，建議一個 DRG 群組內部審查：

如果 AMI 明確或有事件的強烈支持： a. 若有任何主要併發症(complex) → DRG 121 b. 否則，若有併發症 → DRG 122 c.否則 → DRG 123

如果不支持 AMI：a. 伴有急性臨床事件的 CAD → DRG 124 b.僅限 CAD → DRG 125 

【任務要求】
1. 先重建主要臨床事件（重點事件即可）
2. 判斷是否主診為 CAD
3. 若為 CAD，判斷是否併發症（需明確事件支持）
4. 列出所有推薦的 ICD 診斷碼（最多10個）

【輸出格式】（必須完全遵守，不要加其他標題）
【CAD 判斷結果】
是否主診為 CAD：是 / 否
是否併發症：是 / 否
預估 DRG：124 或 125
預估 RW：1.0448 或 0.7146
關鍵證據：
1. [事件描述，20字內]
2. [事件描述，20字內]

【一般 ICD 推薦】
1. I25.110 - Atherosclerotic heart disease of native coronary artery with unstable angina pectoris(自體的冠狀動脈粥樣硬化心臟病伴有不穩定心絞痛)
   原因：[限20字，來自明確事件]
2. I50.20 - Unspecified systolic (congestive) heart failure(未明示收縮性(充血性)心臟衰竭)
   原因：...
...

【嚴格格式要求】
- 原因必須直接來自事件，不能推測
"""

# 儲存 Prompt（上限 20 個）
# 1. 指定您想要的資料夾路徑
SAVE_DIR = r"C:\Users\482525\Prompt_File"
# 2. 指定完整檔案路徑
PROMPT_FILE = os.path.join(SAVE_DIR, 'saved_icd_prompts.json')

def load_from_file():
    # 如果檔案夾或檔案不存在，回傳空列表
    if os.path.exists(PROMPT_FILE):
        try:
            with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"讀取錯誤: {e}")
            return []
    return []

def save_to_file(prompts):
    # 自動檢查資料夾是否存在，不存在就建立它
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        
    with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
        # ensure_ascii=False 確保中文字不會變成編碼，indent=4 讓格式好看
        json.dump(prompts, f, ensure_ascii=False, indent=4)

# 儲存 ICD Prompt
@icd_bp.route('/save_icd_prompt', methods=['POST'])
def save_icd_prompt():
    data = request.json
    name = data.get('name', '').strip() or "未命名 ICD Prompt"
    prompt = data.get('prompt', '').strip()
    
    if not prompt:
        return jsonify({"error": "Prompt 內容不可為空"}), 400
    
    # 讀取現有
    prompts = []
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
    
    # 移除同名（避免重複）
    prompts = [p for p in prompts if p['name'] != name]
    
    # 新增
    prompts.append({"name": name, "prompt": prompt})
    
    # 上限 10 個
    if len(prompts) > 10:
        prompts = prompts[-10:]
    
    # 寫回
    with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True})

# 載入 ICD Prompt 列表
@icd_bp.route('/load_icd_prompts')
def load_icd_prompts():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
    else:
        prompts = []
    return jsonify({"prompts": prompts})

@icd_bp.route('/generate_icd', methods=['POST'])
def generate_icd():
    if request.json is None:
        return jsonify({"error": "無效的 JSON 資料"}), 400
    
    data = request.json
    
    # 關鍵修正：欄位名稱改成前端新 ID
    case_text = data.get('case_text', '').strip()
    discharge_summary = data.get('discharge', '').strip()
    custom_prompt = (data.get('prompt') or '').strip()
    
    if not case_text:
        return jsonify({"error": "請輸入病例文字"}), 400
    
    try:
        full_input = f"【病例文字】\n{case_text}"
        if discharge_summary:
            full_input += f"\n\n【出院摘要】\n{discharge_summary}"
        
        system_prompt = CAD_ANALYSIS_PROMPT  # 你的 CAD Prompt
        if custom_prompt:
            system_prompt = f"{custom_prompt}\n\n{system_prompt}"
        
        client, deployment = get_client_and_deployment()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_input}
        ]
        
        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=0.0,
            max_tokens=1500
        )
        
        llm_output = response.choices[0].message.content.strip()
        final_output = post_process_icd_with_cad(llm_output)
        
        history = messages + [{"role": "assistant", "content": llm_output}]
        
        return jsonify({
            "answer": final_output,
            "history": history
        })
        
    except Exception as e:
        return jsonify({"error": f"處理失敗：{str(e)}"}), 500