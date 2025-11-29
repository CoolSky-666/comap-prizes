import re
import sys
import csv
from collections import Counter
import PyPDF2
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

# -----------------------------------
# 奖项定义
# -----------------------------------
AWARDS = [
    "Outstanding Winner",
    "Finalist",
    "Meritorious Winner",
    "Honorable Mention",
    "Successful Participant",
    "Unsuccessful",
    "Disqualified",
    "Not Judged"
]

AWARD_SHORT = {
    "Outstanding Winner": "O",
    "Finalist": "F",
    "Meritorious Winner": "M",
    "Honorable Mention": "H",
    "Successful Participant": "S",
    "Unsuccessful": "U",
    "Disqualified": "D",
    "Not Judged": "N"
}

# 正则容错空格换行
award_pat = re.compile('|'.join(
    re.sub(r'\s+', r'\\s+', re.escape(a)) for a in AWARDS
), re.I)

# -----------------------------------
def extract_designations(pdf_path: str):
    """读取 PDF 并提取奖项关键字"""
    designations = []
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[1:]:  # 跳过第一页封面
                text = page.extract_text() or ""
                for m in award_pat.finditer(text):
                    designations.append(m.group(0))
    except Exception as e:
        print(f"[错误] 读取失败: {pdf_path} - {e}")
    return designations

# -----------------------------------
def process_pdf_worker(year, problem, pdf_path, contest_type):
    """工作进程：处理单个 PDF"""
    designations = extract_designations(pdf_path)
    if not designations:
        return year, problem, contest_type, None  # None 表示无提取

    counter = Counter(designations)
    rows = []
    for aw in AWARDS:
        rows.append([year, problem, contest_type, AWARD_SHORT[aw], counter.get(aw, 0)])
    return year, problem, contest_type, rows

# -----------------------------------
def main():
    start_year = 2023
    end_year = 2025
    base_dir = "Contest_PDFs"
    problems_mcm = ["A", "B", "C"]
    problems_icm = ["D", "E", "F"]

    tasks = []

    # 组装任务列表
    for year in range(start_year, end_year + 1):
        for prob in problems_mcm:
            pdf_path = os.path.join(base_dir, "MCM", f"{year}_MCM_Problem_{prob}_Results.pdf")
            if os.path.exists(pdf_path):
                tasks.append((year, prob, pdf_path, "MCM"))
        for prob in problems_icm:
            pdf_path = os.path.join(base_dir, "ICM", f"{year}_ICM_Problem_{prob}_Results.pdf")
            if os.path.exists(pdf_path):
                tasks.append((year, prob, pdf_path, "ICM"))

    if not tasks:
        print("[错误] 没有找到任何 PDF 文件")
        sys.exit(1)

    all_results = []

    # 根据CPU核心数自动选择最大并发
    max_workers = os.cpu_count() or 4
    print(f"\n🚀 使用并行处理（进程数：{max_workers}）...")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_pdf_worker, *task): task for task in tasks}
        for fut in as_completed(futures):
            year, prob, _, _ = futures[fut]
            try:
                result = fut.result()
                if result[3] is None:
                    print(f"[警告] 未提取到奖项: {year}-Problem {prob}")
                    continue
                all_results.extend(result[3])
                print(f"[完成] {year}-Problem {prob}")
            except Exception as e:
                print(f"[错误] 处理失败 {year}-Problem {prob}: {e}")

    if not all_results:
        print("\n❌ 未提取到任何奖项")
        sys.exit(1)

    # 输出 CSV
    csv_name = f"{start_year}-{end_year}-MCM-ICM-Results.csv"
    with open(csv_name, "w", newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Year", "Problem", "Type", "Award", "Count"])
        writer.writerows(all_results)

    print(f"\n🎯 所有年份数据已写入文件：{csv_name}")

# -----------------------------------
if __name__ == "__main__":
    main()
