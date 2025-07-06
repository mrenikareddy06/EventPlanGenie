# utils/scheduler_utils.py

from typing import Dict, List
import re
from datetime import datetime

class SchedulerUtils:
    @staticmethod
    def extract_schedule_sections(markdown: str) -> List[Dict[str, str]]:
        sections = []
        day_blocks = re.split(r'(?=^## Day \d+)', markdown, flags=re.MULTILINE)
        for block in day_blocks:
            date_match = re.search(r'Day (\d+) \u2014 (\d{4}-\d{2}-\d{2})', block)
            table_match = re.search(r'(\| Time \| Duration \| Activity \| Vendor/Resource \|.*?\|\s*$)', block, re.DOTALL | re.MULTILINE)
            if date_match:
                day = date_match.group(1)
                date = date_match.group(2)
                table = table_match.group(1).strip() if table_match else ""
                sections.append({"day": day, "date": date, "table": table})
        return sections

    @staticmethod
    def validate_schedule_block(markdown: str) -> bool:
        return 'Time | Duration | Activity | Vendor/Resource' in markdown

    @staticmethod
    def summarize_schedule_timing(markdown: str) -> Dict[str, str]:
        time_pattern = re.compile(r'\|\s*(\d{1,2}:\d{2})\s*\|')
        times = time_pattern.findall(markdown)
        if not times:
            return {"earliest": "N/A", "latest": "N/A"}
        times_24 = [datetime.strptime(t, "%H:%M") for t in times if len(t) == 5]
        times_24.sort()
        return {
            "earliest": times_24[0].strftime("%H:%M"),
            "latest": times_24[-1].strftime("%H:%M")
        }

    @staticmethod
    def estimate_schedule_hours(markdown: str) -> float:
        durations = re.findall(r'\|\s*\d{1,2}:\d{2}\s*\|\s*(\d+(?:\.\d+)?)\s*\|', markdown)
        total = sum(float(d) for d in durations)
        return round(total, 2)
