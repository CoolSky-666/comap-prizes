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
    
import re

def clean_pdf_text(raw_text: str) -> str:
    """
    清洗由 PDF 提取出的 ICM/MCM 比赛结果文本：
    - 去掉退格符、控制符
    - 修复断词、连续字母
    - 标准化奖项名称
    """
    text = raw_text

    # 🔹 1. 去掉退格符和多余控制符
    text = re.sub(r'\\x08', '', text)           # 去除退格符显式转义
    text = re.sub(r'\x08', '', text)            # 去除实际退格符
    text = re.sub(r'[\r\n]+', ' ', text)        # 合并换行符为空格
    text = re.sub(r'\s{2,}', ' ', text)         # 压缩多余空格

    # 🔹 2. 修复字母之间多余空格 (例如 'H o n o r a b l e' → 'Honorable')
    # 合并连续英文字符间的空格，只对大写或小写字母之间的空格
    text = re.sub(r'(?<=\b[A-Za-z])\s+(?=[A-Za-z]\b)', '', text)

    # 🔹 3. 统一空格
    text = re.sub(r'\s{2,}', ' ', text).strip()

    # 🔹 4. 替换反常断词
    replacements = {
        "Outsta nding": "Outstanding",
        "Merit orious": "Meritorious",
        "Honorab le": "Honorable",
        "Su ccessful": "Successful",
        "Parti cipant": "Participant",
        "Not Judg ed": "Not Judged",
        "Jud ged": "Judged",
        "Disqua lified": "Disqualified",
        "WinnerDisqualified": "Winner Disqualified",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    # 🔹 5. 标准化奖项短语 (去掉空格丢失的情况)
    normalize_awards = {
        "OutstandingWinner": "Outstanding Winner",
        "MeritoriousWinner": "Meritorious Winner",
        "HonorableMention": "Honorable Mention",
        "SuccessfulParticipant": "Successful Participant",
        "NotJudged": "Not Judged",
        "Disqualified": "Disqualified",
        "FinalistAward": "Finalist",
        "FinalistWinner": "Finalist",
    }
    for k, v in normalize_awards.items():
        text = text.replace(k, v)

    # 🔹 6. 防止大小写混乱
    # 把所有奖项关键字首字母统一大写
    for word in [
        "Outstanding Winner", "Meritorious Winner", "Honorable Mention",
        "Successful Participant", "Not Judged", "Disqualified", "Finalist"
    ]:
        pattern = re.compile(word, re.I)
        text = pattern.sub(word, text)

    # 🔹 7. 再次去掉多余空格
    text = re.sub(r'\s{2,}', ' ', text).strip()

    return text


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
    start_year = end_year = 2018

    problems_mcm = []
    problems_icm = ["D"]

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
