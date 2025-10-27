# classifier.py
import re
from difflib import get_close_matches
# placeholder keyword lists
KEYWORDS = {
  "utilities": ["electric", "water", "coned", "comcast", "verizon", "internet"],
  "groceries": ["grocery", "market", "whole foods", "safeway", "trader joe"],
  "savings": ["transfer to savings", "deposit to savings"],
  "social": ["restaurant", "bar", "cafe", "netflix", "spotify"],
  "transportation": ["uber", "lyft", "shell", "exxon", "bus", "train"],
  "housing": ["rent", "mortgage", "landlord"]
}

def normalize_text(s):
    return s.lower()

def rule_classify(description):
    s = normalize_text(description)
    for cat, words in KEYWORDS.items():
        for w in words:
            if w in s:
                return cat, 0.95
    return None, None

# If rule_classify returns None, call AI fallback (OpenAI or other)
def ai_classify_openai(description, openai_client, categories):
    """
    Example: send a concise prompt asking to choose one of categories.
    Return (category_name, confidence)
    """
    # Build prompt...
    # call openai.ChatCompletion.create(...) or v1/completions
    # parse response -> category
    # return category, confidence
    raise NotImplementedError("Add your OpenAI call here following your api client")
