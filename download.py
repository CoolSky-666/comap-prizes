#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from time import sleep

'''
以下文件格式不统一，需要单独下载:
default: {year}_ICM_Problem_{problem}_Results.pdf
"-"
2016-ICM_Problem-D-Results.pdf
2016-ICM_Problem-E-Results.pdf
2016-ICM_Problem-F-Results.pdf
"%20"
2021_ICM%20Problem_D_Results.pdf
2021_ICM%20Problem_E_Results.pdf
2021_ICM%20Problem_F_Results.pdf
"R -> r"
2022_MCM_Problem_A_results.pdf
2022_MCM_Problem_B_results.pdf
2022_MCM_Problem_C_results.pdf
"%20"
2022_ICM%20Problem_D_Results.pdf
2022_ICM%20Problem_E_Results.pdf
2022_ICM%20Problem_F_Results.pdf
'''

def download_contest_pdfs(start_year=2022, end_year=2022):
    base_urls = {
        "MCM": "https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/results/{year}_MCM_Problem_{problem}_Results.pdf",
        "ICM": "https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/results/{year}_ICM_Problem_{problem}_Results.pdf"
    }

    base_urls = {
        "MCM": "https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/results/{year}_MCM_Problem_{problem}_results.pdf",
        "ICM": "https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/results/{year}_ICM%20Problem_{problem}_Results.pdf"
    } # 2022
  
    problems = {
        "MCM": ["A", "B", "C"],
        "ICM": ["D", "E", "F"]
    }

    save_root = "Contest_PDFs"
    os.makedirs(save_root, exist_ok=True)

    for contest_type, url_template in base_urls.items():
        print(f"\n=== 正在下载 {contest_type} PDF 文件 ===")
        save_dir = os.path.join(save_root, contest_type)
        os.makedirs(save_dir, exist_ok=True)

        for year in range(start_year, end_year + 1):
            for problem in problems[contest_type]:
                url = url_template.format(year=year, problem=problem)
                filename = f"{year}_{contest_type}_Problem_{problem}_Results.pdf"
                save_path = os.path.join(save_dir, filename)

                print(f"正在下载: {url}")
                try:
                    response = requests.get(url, timeout=20)
                    # 判断返回内容是否为 PDF
                    if response.status_code == 200 and response.content.startswith(b"%PDF"):
                        with open(save_path, "wb") as f:
                            f.write(response.content)
                        print(f"✅ 已保存: {save_path}")
                    else:
                        print(f"⚠️ 文件不存在或不是 PDF: {url} (状态码: {response.status_code})")
                except requests.RequestException as e:
                    print(f"❌ 下载失败: {url}\n错误信息: {e}")
                sleep(0.1)  # 避免请求过快
    
    print("\n🎯 所有年份题目文件下载完成！")

if __name__ == "__main__":
    download_contest_pdfs()
