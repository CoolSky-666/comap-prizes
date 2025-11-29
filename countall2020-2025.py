import re
import sys
import csv
from collections import Counter
import PyPDF2
import os
'''
奖项定义: 2020-2025 正常读取(MCM-ABC,ICM-DEF)

2015年只有ABCD题, AB为MCM, CD为ICM, 故没有爬取之前的数据
不考虑2023年“春季赛”的Y题(二手帆船价格评估) 与 Z题(奥运会未来规划)

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


award_pat = re.compile('|'.join(map(re.escape, AWARDS)), re.I)

# -----------------------------------
# PDF 解析函数
# -----------------------------------
def extract_designations(pdf_path: str):
    """返回所有奖项关键字出现次数列表"""
    designations = []
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[1:]:  # 通常第一页是封面，从第二页开始
                text = page.extract_text() or ""
                # print(text)
                for m in award_pat.finditer(text):
                    designations.append(m.group(0))
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

# -----------------------------------
# 主函数
# -----------------------------------
def main():
    start_year = 2020
    end_year = 2025

    problems_mcm = ["A", "B", "C"]
    problems_icm = ["D", "E", "F"]
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

    # 输出 CSV 文件
    csv_name = "MCM-ICM-Results.csv"
    with open(csv_name, "a", newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Year", "Problem", "Type", "Award", "Count"])
        writer.writerows(all_results)

    print(f"\n🎯 所有年份数据已写入文件：{csv_name}")

# -----------------------------------
if __name__ == "__main__":
    main()
