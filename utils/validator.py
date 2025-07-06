# shared/validator.py

import re
import requests
from urllib.parse import urlparse
from typing import Union, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# === URL, Email, Phone Validation ===

def is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    pattern = re.compile(
        r'^https?://(?:[\w-]+\.)+[a-z]{2,6}(/\S*)?$', re.IGNORECASE
    )
    if not pattern.match(url):
        return False
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except:
        return False

def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}$', email))

def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r'\D', '', phone)
    patterns = [r'^91[6-9]\d{9}$', r'^[6-9]\d{9}$', r'^0[6-9]\d{9}$']
    return any(re.match(p, digits) for p in patterns)

# === Input Field Validation ===

def validate_event_inputs(inputs: Dict[str, Any]) -> Dict[str, List[str]]:
    errors = {}
    required = ['event_name', 'event_type', 'location', 'start_date', 'end_date']
    for field in required:
        if not inputs.get(field):
            errors.setdefault('required', []).append(f"{field.replace('_', ' ').title()} is required")

    try:
        start = datetime.strptime(inputs['start_date'], '%Y-%m-%d')
        end = datetime.strptime(inputs['end_date'], '%Y-%m-%d')
        if start > end:
            errors.setdefault('dates', []).append("Start date cannot be after end date")
        if start.date() < datetime.now().date():
            errors.setdefault('dates', []).append("Start date cannot be in the past")
    except:
        errors.setdefault('dates', []).append("Invalid date format. Use YYYY-MM-DD")

    if 'price_range' in inputs:
        try:
            pr = list(map(float, inputs['price_range']))
            if pr[0] < 0 or pr[1] < 0:
                errors.setdefault('budget', []).append("Budget values cannot be negative")
            if pr[0] > pr[1]:
                errors.setdefault('budget', []).append("Min budget cannot exceed max budget")
        except:
            errors.setdefault('budget', []).append("Invalid price range format")

    return errors

# === Text and Extraction Utilities ===

def sanitize_text(text: str, max_length: int = 500) -> str:
    if not text: return ""
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned[:max_length].rsplit(' ', 1)[0] + "..." if len(cleaned) > max_length else cleaned

def extract_contacts_from_text(text: str) -> Dict[str, List[str]]:
    emails = re.findall(r'\b[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}\b', text)
    phones = re.findall(r'\+?91[-\s]?[6-9]\d{9}|[6-9]\d{9}', text)
    phones_clean = list(set(re.sub(r'\D', '', p) for p in phones if is_valid_phone(p)))
    return {"emails": list(set(emails)), "phones": phones_clean}

# === Currency ===

def format_currency(amount: Union[int, float], currency: str = "₹") -> str:
    try:
        amount = float(amount)
        if amount >= 1e7: return f"{currency}{amount/1e7:.1f}Cr"
        elif amount >= 1e5: return f"{currency}{amount/1e5:.1f}L"
        elif amount >= 1e3: return f"{currency}{amount/1e3:.1f}K"
        return f"{currency}{amount:,.0f}"
    except:
        return f"{currency}0"

# === Venue & Vendor Block Validators ===

def validate_venue_block(text: str) -> Dict[str, Any]:
    lines = text.splitlines()
    result = {"name": "", "cost": "", "contact_info": {}, "link": "", "description": "", "valid": False, "errors": []}
    result["name"] = re.sub(r'[\*\*]', '', lines[0].split(' - ')[0]).strip() if lines else ""
    result["contact_info"] = extract_contacts_from_text(text)
    for line in lines:
        if 'link:' in line.lower():
            url = line.split(':', 1)[1].strip()
            if is_valid_url(url):
                result["link"] = url
            else:
                result["errors"].append("Invalid URL")
    cost_match = re.findall(r'₹[\d,.]+', text)
    result["cost"] = cost_match[0] if cost_match else ""
    if not result["name"]: result["errors"].append("Missing venue name")
    if not result["contact_info"]["emails"] and not result["contact_info"]["phones"]:
        result["errors"].append("Missing contact info")
    if not result["link"]: result["errors"].append("Missing link")
    result["valid"] = len(result["errors"]) == 0
    return result

def validate_vendor_block(text: str) -> Dict[str, Any]:
    lines = text.splitlines()
    result = {"name": "", "services": [], "cost": "", "contact_info": {}, "link": "", "valid": False, "errors": []}
    result["name"] = re.sub(r'[\*\*]', '', lines[0].split(' - ')[0]).strip() if lines else ""
    for line in lines:
        if 'includes:' in line.lower():
            services = re.split(r'[;,]', line.split(':', 1)[-1])
            result["services"] = [s.strip() for s in services if s.strip()]
    result["contact_info"] = extract_contacts_from_text(text)
    for line in lines:
        if 'link:' in line.lower():
            url = line.split(':', 1)[-1].strip()
            if is_valid_url(url):
                result["link"] = url
            else:
                result["errors"].append("Invalid URL")
    cost_match = re.findall(r'₹[\d,.]+', text)
    result["cost"] = cost_match[0] if cost_match else ""
    if not result["name"]: result["errors"].append("Missing name")
    if not result["services"]: result["errors"].append("Missing services")
    if not result["contact_info"]["emails"] and not result["contact_info"]["phones"]:
        result["errors"].append("Missing contact info")
    result["valid"] = len(result["errors"]) == 0
    return result

# === Wrapper Class ===
class Validator:
    def validate_all(self, inputs: Dict[str, Any], stage: str = 'basic') -> Dict[str, Any]:
        result = {"valid": True, "errors": {}, "warnings": {}, "sanitized_inputs": {}}
        base_errors = validate_event_inputs(inputs)
        if base_errors:
            result["errors"].update(base_errors)
            result["valid"] = False
        for f in ['event_name', 'description', 'location']:
            if inputs.get(f):
                result["sanitized_inputs"][f] = sanitize_text(inputs[f])
        if stage == 'venue_selection' and inputs.get('selected_venue'):
            venue = validate_venue_block(inputs['selected_venue'])
            if not venue['valid']:
                result["errors"]["venue"] = venue['errors']
                result["valid"] = False
        if stage == 'vendor_selection' and inputs.get('selected_vendor'):
            vendor = validate_vendor_block(inputs['selected_vendor'])
            if not vendor['valid']:
                result["errors"]["vendor"] = vendor['errors']
                result["valid"] = False
        return result

    def get_validation_summary(self, result: Dict[str, Any]) -> str:
        if result["valid"]:
            return "✅ All inputs are valid!"
        lines = ["❌ Validation failed:"]
        for k, errs in result["errors"].items():
            lines.append(f"**{k.title()} Issues:**")
            lines.extend([f"  • {e}" for e in errs])
        return "\n".join(lines)

# === Backward Compatibility ===
def validate_inputs(inputs: Dict[str, Any]) -> bool:
    return Validator().validate_all(inputs)["valid"]

def clean_text(text: str) -> str:
    return sanitize_text(text)
