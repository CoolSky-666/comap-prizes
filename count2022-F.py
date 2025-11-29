import re
import sys
import csv
from collections import Counter
import PyPDF2
import os
'''
奖项定义: 2020-2025 正常读取

2015年只有ABCD题, AB为MCM, CD为ICM, 故没有爬取之前的数据

2016:
没有 "Disqualified" 或 "Not Judged"
Outstanding  Winner
Finalist
Meritorious  Winner
Honorab le Mention
Successful  Participant
Unsuccessful

2017/2018
没有 "Not Judged"
Outstanding  Winner
Finalist
Meritorious  Winner
Honorab le Mention
Successful  Participant
Unsuccessful
Disqualified

2019
Unsuccessful - W(Web) 比赛期间队员访问了公开讨论赛题的网站/社交媒体
Unsuccessful - I(Incomplete) 提交的论文严重不完整，或完全没有回应赛题要求
Disqualified - P(Plagiarism) 论文被判定存在抄袭或未标注来源的内容
依旧没有 "Not Judged"
2019的格式错误有些严重，AI给出的解决方案与2016-2018的处理不同

'''

AWARDS = [
    "Outstanding Winner",
    "Finalist",
    "Meritorious Winner",
    "Honorable Mention",
    "Successful Participant",
    "Unsuccessful",
    "Disqualified",
    "Not Judged"
] # 2020-2025

AWARD_SHORT = {
    "Outstanding Winner": "O",
    "Finalist": "F",
    "Meritorious Winner": "M",
    "Honorable Mention": "H",
    "Successful Participant": "S",
    "Unsuccessful": "U",
    "Disqualified": "D",
    "Not Judged": "N"
} # 2020-2025

award_pat = re.compile(
    r'(Outstanding\s*Winner|Meritorious\s*Winner|Honorable\s*Mention|Successful\s*Participant|Finalist|Not\s*Judged|Disqualified|Unsuccessful)',
    re.I
)



def normalize_award(word: str):
    word_low = word.lower()
    if "outstanding" in word_low:
        return "Outstanding Winner"
    elif "finalist" in word_low:
        return "Finalist"
    elif "meritorious" in word_low:
        return "Meritorious Winner"
    elif "honora" in word_low:
        return "Honorable Mention"
    elif "successful" in word_low and "un" not in word_low:
        return "Successful Participant"
    elif "unsuccessful" in word_low:
        return "Unsuccessful"
    elif "disqualified" in word_low:
        return "Disqualified"
    elif "not" in word_low and "judged" in word_low:
        return "Not Judged"
    else:
        return None
    
def clean_pdf_text(text: str) -> str:
    import re

    # 1️⃣ 清理乱码字符
    text = text.replace("\x00", "")
    text = re.sub(r"[\u4E00-\u9FFF\uE000-\uF8FF]", "", text)
    for ws in ["\u00A0", "\u202F", "\u3000", "\xa0"]:
        text = text.replace(ws, " ")

    # 2️⃣ 全角转半角
    def to_halfwidth(s: str):
        res = []
        for ch in s:
            code = ord(ch)
            if code == 0x3000:
                res.append(' ')
            elif 0xFF01 <= code <= 0xFF5E:
                res.append(chr(code - 0xFEE0))
            else:
                res.append(ch)
        return ''.join(res)
    text = to_halfwidth(text)

    # 3️⃣ 去掉字母组之间的逗号（更宽松匹配：只要是字母间的逗号或空格都删掉）
    text = re.sub(r'(?<=[A-Za-z])[,\s]+(?=[A-Za-z])', '', text)

    # 有时会出现 " , " → " "
    text = text.replace(', ', ' ')
    # 多余空格合并
    text = re.sub(r'\s+', ' ', text)

    # 4️⃣ 修正断词（根据常见错误）
    replacements = {
        "Honorab le": "Honorable",
        "Honora ble": "Honorable",
        "Merit orious": "Meritorious",
        "Suc cessful": "Successful",
        "Parti cipant": "Participant",
        "Re sults": "Results",
        "Univ ersity": "University",
        "Informa tion": "Information",
        "Tech nology": "Technology",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    return text.strip()

# -----------------------------------
# PDF 解析函数
# -----------------------------------
def extract_designations(pdf_path: str):
    designations = []
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages[1:], start=2):
                raw_text = page.extract_text() or ""
                text = clean_pdf_text(raw_text)  # 🧹 清洗关键步骤
                # print(text)
                for m in award_pat.finditer(text):
                    award_full = normalize_award(m.group(0))
                    if award_full:
                        designations.append(award_full)
                        # print(f"[匹配成功] → {award_full}")
    except Exception as e:
        print(f"[错误] 无法读取 PDF: {pdf_path} - {e}")
    return designations

def process_pdf(year: int, problem: str, pdf_path: str, contest_type: str):
    """处理单个PDF并返回统计结果"""
    designations = extract_designations(pdf_path)
    if not designations:
        print(f"[警告] 未提取到任何奖项：{pdf_path}")
        return []

    counter = Counter(designations)

    # 打印统计
    print(f"\n=== {pdf_path} ({contest_type}) 统计结果 ===")
    print(f"{'Award':<20}  {'Count':>5}")
    print("-" * 30)
    for aw in AWARDS:
        print(f"{aw:<20}  {counter.get(aw, 0):>5}")
    print("-" * 30)

    # 拼接结果行
    result_rows = []
    for aw in AWARDS:
        result_rows.append([
            year,
            problem,
            contest_type,
            AWARD_SHORT[aw],
            counter.get(aw, 0)
        ])
    return result_rows

def main():
    start_year = 2022
    end_year = 2022

    problems_mcm = []
    problems_icm = ["F"]

    all_results = []

    for year in range(start_year, end_year + 1):
        print(f"\n========== 处理 {year} 年 ==========")

        # --- 处理 MCM ---
        for prob in problems_mcm:
            pdf_path = f'Contest_PDFs/MCM/{year}_MCM_Problem_{prob}_Results.pdf'
            if not os.path.exists(pdf_path):
                print(f"[错误] 文件不存在：{pdf_path}")
                continue
            # print(f"正在处理 {pdf_path} ...")
            rows = process_pdf(year, prob, pdf_path, "MCM")
            all_results.extend(rows)

        # --- 处理 ICM ---
        for prob in problems_icm:
            pdf_path = f'Contest_PDFs/ICM/{year}_ICM_Problem_{prob}_Results.pdf'
            if not os.path.exists(pdf_path):
                print(f"[错误] 文件不存在：{pdf_path}")
                continue
            rows = process_pdf(year, prob, pdf_path, "ICM")
            all_results.extend(rows)

    if not all_results:
        print("\n未提取到任何奖项，请检查 PDF 文件内容")
        sys.exit(1)

    # 输出 CSV 文件（追加模式）
    csv_name = "MCM-ICM-Results.csv"
    file_exists = os.path.exists(csv_name)
    with open(csv_name, "a", newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Year", "Problem", "Type", "Award", "Count"])
        writer.writerows(all_results)

    print(f"\n🎯 所有年份数据已写入文件：{csv_name}")

# -----------------------------------
if __name__ == "__main__":
    main()
