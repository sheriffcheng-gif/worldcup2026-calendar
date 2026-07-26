#!/usr/bin/env python3
"""
美职联(MLS) 2026 赛程日历生成器
从 fixturedownload.com 获取赛程 ICS，翻译成中文
"""

import re
import urllib.request
from datetime import datetime, timezone, timedelta

# MLS 2026 ICS URL
MLS_ICS_URL = "https://fixturedownload.com/download/mls-2026-UTC.ics"

# MLS 球队名 英文 -> 中文
TEAMS_CN = {
    "Atlanta United": "亚特兰大联",
    "Austin FC": "奥斯汀FC",
    "CF Montréal": "蒙特利尔CF",
    "Charlotte FC": "夏洛特FC",
    "Chicago Fire FC": "芝加哥火焰",
    "Colorado Rapids": "科罗拉多急流",
    "Columbus Crew": "哥伦布机员",
    "D.C. United": "华盛顿联",
    "FC Cincinnati": "辛辛那提FC",
    "FC Dallas": "达拉斯FC",
    "Houston Dynamo FC": "休斯顿迪纳摩",
    "Inter Miami CF": "迈阿密国际",
    "LA Galaxy": "洛杉矶银河",
    "Los Angeles Football Club": "洛杉矶FC",
    "Minnesota United FC": "明尼苏达联",
    "Nashville SC": "纳什维尔SC",
    "New England Revolution": "新英格兰革命",
    "New York City Football Club": "纽约城FC",
    "Orlando City": "奥兰多城",
    "Philadelphia Union": "费城联合",
    "Portland Timbers": "波特兰伐木者",
    "Real Salt Lake": "皇家盐湖城",
    "Red Bull New York": "纽约红牛",
    "San Diego FC": "圣迭戈FC",
    "San Jose Earthquakes": "圣何塞地震",
    "Seattle Sounders FC": "西雅图海湾人",
    "Sporting Kansas City": "堪萨斯城竞技",
    "St. Louis CITY SC": "圣路易斯城",
    "Toronto FC": "多伦多FC",
    "Vancouver Whitecaps FC": "温哥华白浪",
}

# 需特殊处理的名称包含 "FC"、"SC" 的
# Sporting Kansas City 保持原名
# Los Angeles Football Club → 简称洛杉矶FC


def translate_team(name):
    """翻译球队名"""
    if not name:
        return name
    # 精确匹配（长度降序避免部分匹配）
    for en, cn in sorted(TEAMS_CN.items(), key=lambda x: -len(x[0])):
        if name.strip() == en:
            return cn
    return name


def fetch_ics_text(url):
    """下载 ICS 文件内容"""
    req = urllib.request.Request(url, headers={"User-Agent": "MLS2026Calendar/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8")
    return raw


def generate_mls_ics(ics_text):
    """解析并翻译 MLS ICS"""
    lines_out = []
    lines = ics_text.split("\r\n")

    current_event = []
    in_event = False
    event_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测事件开始/结束
        if line == "BEGIN:VEVENT":
            in_event = True
            current_event = [line]
            continue
        elif line == "END:VEVENT":
            in_event = False
            current_event.append(line)
            # 处理这个事件
            processed = process_event(current_event)
            lines_out.extend(processed)
            event_count += 1
            current_event = []
            continue

        if in_event:
            current_event.append(line)
        else:
            lines_out.append(line)

    print(f"Processed {event_count} events")
    return "\r\n".join(lines_out)


def process_event(event_lines):
    """翻译单个 VEVENT 的内容"""
    result = []
    for line in event_lines:
        if line.startswith("SUMMARY:"):
            summary = line[8:]
            translated = translate_summary(summary)
            result.append(f"SUMMARY:{translated}")
        elif line.startswith("DESCRIPTION:"):
            desc = line[12:]
            translated = translate_description(desc)
            result.append(f"DESCRIPTION:{translated}")
        else:
            result.append(line)

    # 添加 UID 前缀标识
    for i, line in enumerate(result):
        if line.startswith("UID:"):
            result[i] = line.replace("UID:", "UID:mls2026-", 1)
            break

    return result


def translate_summary(summary):
    """翻译 SUMMARY 行"""
    # 格式: "Atlanta United vs Austin FC - MLS 2026 Round 1"
    # 用 " vs " 分割，再从右找 " - MLS 2026 "
    vs_idx = summary.find(" vs ")
    sep = " - MLS 2026 "
    mls_idx = summary.find(sep)
    if vs_idx != -1 and mls_idx != -1:
        team1 = summary[:vs_idx].strip()
        team2 = summary[vs_idx + 4:mls_idx].strip()
        round_info = summary[mls_idx + len(sep):].strip()

        t1 = translate_team(team1)
        t2 = translate_team(team2)
        round_cn = translate_round(round_info)

        return f"{t1} vs {t2} - MLS 2026 {round_cn}"

    return summary


def translate_round(round_info):
    """翻译轮次信息"""
    round_cn = round_info

    # Playoffs 等特殊轮次
    round_cn = round_cn.replace("Playoffs", "季后赛")
    round_cn = round_cn.replace("Wild Card", "外卡赛")
    round_cn = round_cn.replace("Conference Semifinals", "分区半决赛")
    round_cn = round_cn.replace("Conference Finals", "分区决赛")
    round_cn = round_cn.replace("MLS Cup", "MLS杯决赛")
    round_cn = round_cn.replace("Leagues Cup", "联赛杯")
    round_cn = round_cn.replace("All-Star Game", "全明星赛")

    # Regular season rounds
    round_cn = re.sub(r'Round (\d+)', r'第\1轮', round_cn)
    round_cn = re.sub(r'Round (\d+)', r'第\1轮', round_cn)

    return round_cn


def translate_description(desc):
    """翻译 DESCRIPTION 行"""
    # 格式: "Atlanta United vs Austin FC\nMLS 2026 Round 1\nMercedes-Benz Stadium\n21/02/2026 19:30 UTC"
    lines = desc.split("\\n")
    result = []
    for l in lines:
        l = l.strip()
        if not l:
            continue

        # 对阵行: "Atlanta United vs Austin FC"
        vs_idx = l.find(" vs ")
        if vs_idx != -1 and " - " not in l:
            t1 = translate_team(l[:vs_idx].strip())
            t2 = translate_team(l[vs_idx + 4:].strip())
            result.append(f"{t1} vs {t2}")
            continue

        # "MLS 2026 Round N" 或 "MLS 2026 Playoffs" 等
        m = re.match(r'^MLS 2026 (.+)$', l)
        if m:
            result.append(f"美职联2026 {translate_round(m.group(1))}")
            continue

        # 场馆、日期等保持原样
        result.append(l)

    return "\\n".join(result)


def main():
    print("Downloading MLS 2026 schedule from fixturedownload.com...")
    ics_text = fetch_ics_text(MLS_ICS_URL)

    print("Translating to Chinese...")
    output = generate_mls_ics(ics_text)

    # 覆盖日历名称
    output = re.sub(
        r'X-WR-CALNAME:.*',
        'X-WR-CALNAME:美职联2026',
        output
    )
    output = re.sub(
        r'X-WR-CALDESC:.*',
        'X-WR-CALDESC:美职联2026赛程（自动更新）',
        output
    )
    output = re.sub(
        r'PRODID:.*',
        'PRODID:-//sheriff//MLS2026 Calendar//CN',
        output
    )

    # 写入文件
    with open("worldcup2026.ics", "w", encoding="utf-8") as f:
        f.write(output)

    # 统计
    events = output.count("BEGIN:VEVENT")
    print(f"Generated worldcup2026.ics ({events} events)")


if __name__ == "__main__":
    main()
