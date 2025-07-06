from .base_agent import BaseAgent
from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class SchedulerAgent(BaseAgent):
    def __init__(self, llm=None):
        prompt = """You are an Event Timeline Coordinator. For each day, generate an hour‑by‑hour schedule.

Input:
- Day {day_num} Date: {date}
- Event: {event_name} ({event_type})
- Theme: {selected_idea}
- Venue: {selected_venue}
- Vendor Services: {selected_vendor_services}
- Time Window: {start_time} to {end_time}

Requirements:
1. Provide table: Time | Duration | Activity | Vendor/Resource
2. Include setup, meals, breaks, theme activities, cleanup.
3. Add buffer between activities.
4. Ensure logical flow and realistic times.

Return as Markdown table.
"""
        super().__init__(
            prompt=prompt,
            name="SchedulerAgent",
            role="Timeline Coordinator",
            model="phi3",
            temperature=0.5
        )

        if llm:
            self.llm = llm

    def create_schedule(self, inputs: Dict[str, str]) -> str:
        try:
            start = datetime.strptime(inputs["start_date"], "%Y-%m-%d")
            end = datetime.strptime(inputs["end_date"], "%Y-%m-%d")
            days = (end - start).days + 1

            outputs = [f"# 📆 Event Schedule: {inputs['event_name']} ({inputs['event_type']})\n"]
            for i in range(days):
                date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
                day_inputs = inputs.copy()
                day_inputs.update({"day_num": i + 1, "date": date})

                raw_schedule = self.run(day_inputs)
                outputs.append(f"## Day {i + 1} — {date}\n")
                outputs.append(raw_schedule)
                outputs.append("\n")

            return "\n".join(outputs)
        except Exception as e:
            logger.error(f"[SchedulerAgent] Error: {e}")
            return f"⚠️ Could not generate schedule due to: {e}"
