"""
Utility functions for data parsing and normalization.
Handles messy marks formats, HTML stripping, and question ID normalization.
"""

import re
from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML content."""

    def __init__(self):
        super().__init__()
        self._result = []

    def handle_data(self, data):
        self._result.append(data)

    def get_text(self):
        return "".join(self._result).strip()


def strip_html(html_str: str) -> str:
    """Strip HTML tags and return plain text."""
    if not html_str:
        return ""
    extractor = HTMLTextExtractor()
    extractor.feed(html_str)
    return extractor.get_text()


def normalize_question_id(raw_id) -> str:
    """
    Normalize _id field from question_bank.json.
    Handles both {"$oid": "..."} dict format and flat string format.
    """
    if isinstance(raw_id, dict):
        return raw_id.get("$oid", str(raw_id))
    return str(raw_id)


def parse_marks(marks_value) -> dict:
    """
    Parse messy marks field into structured data.

    Handles formats:
      - "68/100"           -> net=68, total=100, pct=68.0
      - "28"               -> net=28, total=None, pct=None
      - "+52 -12"          -> net=40, total=None, pct=None
      - "34/75 (45.3%)"    -> net=34, total=75, pct=45.3
      - 72 (int/float)     -> net=72, total=None, pct=None
      - "+48 -8"           -> net=40, total=None, pct=None
      - "39/100"           -> net=39, total=100, pct=39.0
      - "49/120 (40.8%)"   -> net=49, total=120, pct=40.8
    """
    result = {
        "raw": marks_value,
        "net_marks": 0.0,
        "total": None,
        "percentage": None,
    }

    if marks_value is None:
        return result

    # If it's already a number
    if isinstance(marks_value, (int, float)):
        result["net_marks"] = float(marks_value)
        return result

    marks_str = str(marks_value).strip()

    # Format: "34/75 (45.3%)"
    pct_match = re.match(r"([+-]?\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*\((\d+(?:\.\d+)?)%\)", marks_str)
    if pct_match:
        result["net_marks"] = float(pct_match.group(1))
        result["total"] = float(pct_match.group(2))
        result["percentage"] = float(pct_match.group(3))
        return result

    # Format: "68/100"
    frac_match = re.match(r"^([+-]?\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)$", marks_str)
    if frac_match:
        net = float(frac_match.group(1))
        total = float(frac_match.group(2))
        result["net_marks"] = net
        result["total"] = total
        result["percentage"] = round((net / total) * 100, 2) if total > 0 else 0.0
        return result

    # Format: "+52 -12" or "+48 -8"
    plus_minus_match = re.match(r"^\+?\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$", marks_str)
    if plus_minus_match:
        positive = float(plus_minus_match.group(1))
        negative = float(plus_minus_match.group(2))
        result["net_marks"] = positive - negative
        return result

    # Format: plain number as string "28" or "22"
    num_match = re.match(r"^([+-]?\d+(?:\.\d+)?)$", marks_str)
    if num_match:
        result["net_marks"] = float(num_match.group(1))
        return result

    # Fallback - try to extract any number
    numbers = re.findall(r"[+-]?\d+(?:\.\d+)?", marks_str)
    if numbers:
        result["net_marks"] = float(numbers[0])

    return result
