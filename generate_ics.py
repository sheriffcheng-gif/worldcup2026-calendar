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
    """Parse date and time strings into datetime object (UTC)
    Handles formats like "13:00", "13:00 UTC", "13:00 UTC-6", "19:00 UTC+5:30"
    """
    from datetime import timedelta, timezone as tz
    import re
    time_str = time_str.strip()
    utc_offset_hours = 0

    # Match patterns like "13:00 UTC-6" or "13:00 UTC+5:30" or "13:00 UTC" or just "13:00"
    m = re.match(r'(\d{1,2}:\d{2})\s*(?:UTC)?([+-]?\d+(?::\d+)?)?', time_str)
    if m:
        time_part = m.group(1)
        offset_str = m.group(2)
        if offset_str:
            # Parse offset like "-6" or "+5:30"
            parts = offset_str.replace('+', '').split(':')
            offset_hours = int(parts[0])
            offset_minutes = int(parts[1]) if len(parts) > 1 else 0
            utc_offset_hours = offset_hours + (offset_minutes / 60.0 if offset_hours >= 0 else -offset_minutes / 60.0)
    else:
        time_part = time_str.split()[0]  # fallback

    # Parse as local time, then convert to UTC
    # "13:00 UTC-6" → local=13:00, offset=-6 → UTC = 13:00 - (-6h) = 19:00 UTC
    dt_local = datetime.fromisoformat(f"{date_str}T{time_part}:00")
    dt_utc = dt_local - timedelta(hours=utc_offset_hours)
    return dt_utc.replace(tzinfo=tz.utc)


def format_goals(goals):
    """Format goal details for description"""
    if not goals:
        return ""
    parts = []
    for g in goals:
        name = g.get("name", "")
        minute = g.get("minute", "")
        pen = " (点球)" if g.get("penalty") else ""
        og = " (乌龙)" if g.get("owngoal") else ""
        parts.append(f"{name} {minute}'{pen}{og}")
    return ", ".join(parts)


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
        home = translate(match.get("team1", match.get("home", "")))
        away = translate(match.get("team2", match.get("away", "")))
        stage = translate(match.get("stage", match.get("group", "")))
        venue = match.get("ground", match.get("venue", ""))
        city = match.get("city", "")
        country = translate(match.get("country", ""))
        date = match.get("date", "")
        time = match.get("time", "")
        score = match.get("score", {})
        ft = score.get("ft", [])  # full-time: [home, away]
        ht = score.get("ht", [])  # half-time: [home, away]
        goals1 = match.get("goals1", [])
        goals2 = match.get("goals2", [])

        if not date or not time:
            continue

        dt_start = parse_date_time(date, time)
        from datetime import timedelta
        dt_end = dt_start + timedelta(hours=2)

        location = f"{venue}\\, {city}\\, {country}" if city and country else venue

        # Build summary: include score if match played
        if ft and len(ft) == 2:
            summary = f"{home} {ft[0]}-{ft[1]} {away}"
            if stage:
                summary = f"{stage}: {summary}"
            # Add status emoji
            summary = f"⚽ {summary}"
        else:
            summary = f"{home} vs {away}" if home and away else f"比赛 {i}"
            if stage:
                summary = f"{stage}: {summary}"

        # Build description
        desc_lines = [f"阶段: {stage}", f"场地: {location}"]
        if ft and len(ft) == 2:
            desc_lines.append(f"全场比分: {home} {ft[0]} - {ft[1]} {away}")
            if ht and len(ht) == 2:
                desc_lines.append(f"半场比分: {ht[0]} - {ht[1]}")
            if goals1:
                desc_lines.append(f"{home}进球: {format_goals(goals1)}")
            if goals2:
                desc_lines.append(f"{away}进球: {format_goals(goals2)}")
        desc_lines.append(f"自动更新于 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        description = "\\n".join(desc_lines)

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
            # OpenFootball format: either flat list or dict with "matches"/"rounds" key
            if isinstance(data, list):
                all_matches.extend(data)
            elif isinstance(data, dict):
                matches = data.get("matches", data.get("rounds", []))
                if isinstance(matches, list):
                    all_matches.extend(matches)
                # Also check for nested rounds structure
                rounds = data.get("rounds", [])
                if isinstance(rounds, list) and rounds and isinstance(rounds[0], dict) and "matches" in rounds[0]:
                    for round_data in rounds:
                        stage = round_data.get("name", round_data.get("round", ""))
                        for match in round_data.get("matches", []):
                            match["stage"] = stage
                            all_matches.append(match)
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
