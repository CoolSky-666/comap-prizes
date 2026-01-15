历年美赛得奖情况数据集
Recorded the number of winners in each year of the MCM/ICM.
# 统计方法
官网的[历年赛题与结果](https://contest.comap.com/undergraduate/contests/matrix/index.h)中只包含了MCM与ICM总共的各个奖项的人数，爬取各年的pdf文件后，统计附录的表格中的各个奖项名称的出现次数，并与前面的总人数校验，就得到了准确的每年、每个题目、各个奖项的获奖人数，由于pdf的解析问题，不分统计出的总人数与pdf第一页略有偏差(差一个左右)，但可以供大家观察趋势。
![Uploading 8fc6e4e50d725d83d92f99b445f0e323.png…](结果检验)

# 数据标签
- Year(2016-2025)
- Problem(ABCDEF)
- Type(MCM,ICM)
- Award(O,F,M,H,S,U...) 
  - O-Outstanding Winner
  - F-Finalist Winner
  - M-Meritorious Winner
  - H-Honorable Mentions
  - S-Sussessful Participants
  - U-Unsuccessful Participants
  - D-Disqualified
  - N-Not Judged
- Count(number of award winners)

# 数据结果


