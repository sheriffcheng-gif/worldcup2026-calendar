#!/usr/bin/env python3
"""
2026世界杯赛程日历生成器
从 OpenFootball 数据源获取赛程，生成中文 ICS 文件
"""

import json
import re
import urllib.request
from datetime import datetime, timezone

# OpenFootball data URLs (multiple rounds)
DATA_URLS = [
    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json",
]

# Team name English -> Chinese
TEAMS_CN = {
    "Mexico": "墨西哥", "South Africa": "南非", "South Korea": "韩国",
    "Czech Republic": "捷克", "Czechia": "捷克", "Canada": "加拿大",
    "Bosnia and Herzegovina": "波黑", "Bosnia & Herzegovina": "波黑",
    "Qatar": "卡塔尔", "Switzerland": "瑞士", "France": "法国",
    "Netherlands": "荷兰", "Ecuador": "厄瓜多尔", "Venezuela": "委内瑞拉",
    "USA": "美国", "United States": "美国", "England": "英格兰",
    "Wales": "威尔士", "Argentina": "阿根廷", "Brazil": "巴西",
    "Germany": "德国", "Spain": "西班牙", "Portugal": "葡萄牙",
    "Italy": "意大利", "Japan": "日本", "Australia": "澳大利亚",
    "Morocco": "摩洛哥", "Senegal": "塞内加尔", "Tunisia": "突尼斯",
    "Iran": "伊朗", "IR Iran": "伊朗", "Saudi Arabia": "沙特",
    "Uruguay": "乌拉圭", "Colombia": "哥伦比亚", "Nigeria": "尼日利亚",
    "Ghana": "加纳", "Cameroon": "喀麦隆", "Egypt": "埃及",
    "Algeria": "阿尔及利亚", "Ivory Coast": "科特迪瓦",
    "Côte d'Ivoire": "科特迪瓦", "DR Congo": "刚果(金)",
    "Serbia": "塞尔维亚", "Croatia": "克罗地亚", "Poland": "波兰",
    "Denmark": "丹麦", "Belgium": "比利时", "Austria": "奥地利",
    "Turkey": "土耳其", "Türkiye": "土耳其", "Ukraine": "乌克兰",
    "Romania": "罗马尼亚", "Hungary": "匈牙利", "Scotland": "苏格兰",
    "Ireland": "爱尔兰", "Greece": "希腊", "Slovakia": "斯洛伐克",
    "Slovenia": "斯洛文尼亚", "Panama": "巴拿马",
    "Costa Rica": "哥斯达黎加", "Jamaica": "牙买加", "Honduras": "洪都拉斯",
    "New Zealand": "新西兰", "China PR": "中国", "Korea Republic": "韩国",
    "Korea DPR": "朝鲜", "UAE": "阿联酋", "Iraq": "伊拉克",
    "Jordan": "约旦", "Bahrain": "巴林", "Uzbekistan": "乌兹别克斯坦",
    "Indonesia": "印尼", "Tanzania": "坦桑尼亚", "Mali": "马里",
    "Guinea": "几内亚", "Haiti": "海地", "Bolivia": "玻利维亚",
    "Peru": "秘鲁", "Paraguay": "巴拉圭", "Chile": "智利",
}

# Stage name translations
STAGE_CN = {
    "Group A": "A组", "Group B": "B组", "Group C": "C组", "Group D": "D组",
    "Group E": "E组", "Group F": "F组", "Group G": "G组", "Group H": "H组",
    "Group I": "I组", "Group J": "J组", "Group K": "K组", "Group L": "L组",
    "Round of 32": "1/32决赛", "Round of 16": "1/16决赛",
    "Quarter-final": "1/4决赛", "Semi-final": "半决赛",
    "Third place match": "三四名决赛", "Final": "决赛",
}


def translate(name):
    """Translate team/stage name to Chinese"""
    if not name:
        return name
    # Sort by length descending to avoid partial matches
    for en, cn in sorted(TEAMS_CN.items(), key=lambda x: -len(x[0])):
        name = name.replace(en, cn)
    for en, cn in STAGE_CN.items():
        name = name.replace(en, cn)
    return name


def escape_ics(text):
    """Escape text for ICS format"""
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n")
    return text


def fetch_json(url):
    """Fetch JSON from URL"""
    req = urllib.request.Request(url, headers={"User-Agent": "WorldCup2026Calendar/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_date_time(date_str, time_str):
    """Parse date and time strings into datetime object (UTC)"""
    # date format: "2026-06-11", time format: "19:00"
    dt_str = f"{date_str}T{time_str}:00Z"
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def generate_ics(matches):
    """Generate ICS content from match data"""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//sheriff//WorldCup2026 Calendar//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:2026世界杯",
        "X-WR-CALDESC:2026世界杯赛程（自动更新）",
        "X-PUBLISHED-TTL:PT6H",
    ]

    for i, match in enumerate(matches, 1):
        home = translate(match.get("home", ""))
        away = translate(match.get("away", ""))
        stage = translate(match.get("stage", ""))
        venue = match.get("venue", "")
        city = match.get("city", "")
        country = translate(match.get("country", ""))
        date = match.get("date", "")
        time = match.get("time", "")

        if not date or not time:
            continue

        dt_start = parse_date_time(date, time)
        # Assume 2 hours per match
        from datetime import timedelta
        dt_end = dt_start + timedelta(hours=2)

        location = f"{venue}\\, {city}\\, {country}" if city else venue
        summary = f"{home} vs {away}" if home and away else f"比赛 {i}"
        if stage:
            summary = f"{stage}: {summary}"

        description = f"阶段: {stage}\\n场地: {location}\\n自动更新于 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:wc2026-match-{i}",
            f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{escape_ics(summary)}",
            f"LOCATION:{escape_ics(location)}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def main():
    print("Fetching World Cup 2026 data...")

    all_matches = []
    for url in DATA_URLS:
        try:
            data = fetch_json(url)
            # OpenFootball format: array of rounds, each with matches
            rounds = data if isinstance(data, list) else data.get("rounds", data.get("matches", []))
            if isinstance(data, dict) and "rounds" not in data and "matches" not in data:
                # Try to find the data in the top level
                for key, val in data.items():
                    if isinstance(val, list):
                        rounds = val
                        break

            for round_data in rounds:
                if isinstance(round_data, dict):
                    stage = round_data.get("name", "")
                    matches = round_data.get("matches", round_data.get("games", []))
                    for match in matches:
                        match["stage"] = stage
                        all_matches.append(match)
                elif isinstance(round_data, list):
                    all_matches.extend(round_data)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    if not all_matches:
        print("No match data found!")
        return

    print(f"Found {len(all_matches)} matches")

    # Generate ICS
    ics_content = generate_ics(all_matches)

    # Write to file
    with open("worldcup2026.ics", "w", encoding="utf-8") as f:
        f.write(ics_content)

    print(f"Generated worldcup2026.ics ({len(all_matches)} events)")


if __name__ == "__main__":
    main()
