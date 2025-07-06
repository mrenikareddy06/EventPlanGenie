import re
from typing import Dict, Tuple
from agents.reviewer_agent import ReviewerAgent

class ReviewUtils:
    @staticmethod
    def extract_review_summary(reviewed_plan: str) -> Tuple[str, Dict[str, str]]:
        """
        Extract and summarize the ✅ Plan Review section from a Markdown plan.
        Returns:
            - cleaned_plan (str): Full reviewed Markdown plan (can exclude review if needed)
            - summary (dict): Contains 'dates', 'budget', 'timeline', 'map_links', 'recommendations'
        """
        review_pattern = r"(✅ Plan Review.*?)(\n##|\Z)"  # Extract Plan Review block
        match = re.search(review_pattern, reviewed_plan, re.DOTALL | re.IGNORECASE)

        summary = {}
        if match:
            review_block = match.group(1).strip()
            checks = {
                "dates": r"dates match.*?:\s*(yes|no)",
                "budget": r"budget alignment.*?:\s*(yes|no)",
                "timeline": r"timeline feasibility.*?:\s*(yes|no)",
                "map_links": r"map links available.*?:\s*(yes|no)",
                "recommendations": r"recommendations.*?:\s*(.+)"
            }

            for key, pattern in checks.items():
                result = re.search(pattern, review_block, re.IGNORECASE)
                summary[key] = result.group(1).capitalize() if result else "Not Found"

            cleaned_plan = reviewed_plan.strip()  # Optionally remove review block if needed
        else:
            cleaned_plan = reviewed_plan
            summary = {
                "dates": "Missing",
                "budget": "Missing",
                "timeline": "Missing",
                "map_links": "Missing",
                "recommendations": "Missing"
            }

        return cleaned_plan, summary

    @staticmethod
    def review_plan(inputs: Dict) -> Tuple[str, Dict[str, str]]:
        """
        Run the ReviewerAgent to evaluate a full event plan and extract the summary.
        Args:
            inputs (dict): Must contain `full_plan`, `selected_idea`, `selected_venue`, `selected_vendor`
        Returns:
            Tuple of reviewed Markdown plan and a structured summary
        """
        agent = ReviewerAgent()
        reviewed_text = agent.run(inputs)
        return ReviewUtils.extract_review_summary(reviewed_text)
