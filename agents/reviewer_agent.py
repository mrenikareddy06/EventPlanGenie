from .base_agent import BaseAgent
from typing import Dict, Tuple
import re

class ReviewerAgent(BaseAgent):
    def __init__(self, llm=None):
        prompt = """You are a professional event planning reviewer. Review and enhance the complete event plan below.

Event Plan to Review:
{full_plan}

Your tasks:
1. Format with proper Markdown headers (##, ###)
2. Add appropriate emojis for sections: 📋 Overview, 🎨 Ideas, 📍 Venues, 🛍️ Vendors, ⏰ Schedule, 💌 Invitation
3. Check for consistency between selected choices
4. Ensure all sections flow logically
5. Highlight any missing information or improvements needed
6. Make bullet points clear and well-formatted
7. Verify that the schedule matches the selected venue and vendors
8. Ensure all venues and vendor entries include working map links

Selected Choices Summary:
- Idea: {selected_idea}
- Venue: {selected_venue}
- Vendor: {selected_vendor}

Return a complete, well-formatted event plan in Markdown that's ready for presentation or PDF export.
Include a final "✅ Plan Review" section with:
- Consistency check
- Budget alignment
- Timeline feasibility
- Map links available
- Any recommendations
"""
        super().__init__(
            prompt=prompt,
            name="ReviewerAgent",
            role="Event Plan Quality Assurance",
            model="phi3",
            temperature=0.6
        )
        if llm:
            self.llm = llm

    def post_process_review(self, reviewed_plan: str) -> Tuple[str, Dict[str, str]]:
        """
        Extract and validate the ✅ Plan Review section.
        Returns a tuple of (cleaned_plan, review_summary_dict)
        """
        review_pattern = r"(✅ Plan Review.*?)(\n##|\Z)"  # capture until next major section or end
        match = re.search(review_pattern, reviewed_plan, re.DOTALL | re.IGNORECASE)

        review_summary = {}
        if match:
            review_block = match.group(1).strip()

            checks = {
                "dates": r"(dates match.*?:)\s*(yes|no)",
                "budget": r"(budget alignment.*?:)\s*(yes|no)",
                "timeline": r"(timeline feasibility.*?:)\s*(yes|no)",
                "map_links": r"(map links available.*?:)\s*(yes|no)",
                "recommendations": r"(recommendations.*?:)\s*(.+)"
            }

            for key, pattern in checks.items():
                result = re.search(pattern, review_block, re.IGNORECASE)
                if result:
                    review_summary[key] = result.group(2).strip().capitalize()
                else:
                    review_summary[key] = "Not Found"

            cleaned_plan = reviewed_plan.strip()
        else:
            review_summary = {
                "dates": "Missing",
                "budget": "Missing",
                "timeline": "Missing",
                "map_links": "Missing",
                "recommendations": "Missing"
            }
            cleaned_plan = reviewed_plan.strip()

        return cleaned_plan, review_summary


def review_plan(inputs: Dict, llm=None) -> Tuple[str, Dict[str, str]]:
    agent = ReviewerAgent(llm=llm)
    reviewed_text = agent.run(inputs)
    return agent.post_process_review(reviewed_text)
