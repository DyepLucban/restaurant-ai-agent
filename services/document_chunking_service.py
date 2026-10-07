import io, re

def chunk_document(text: str, source: str) -> list[dict]:
    chunks = []

    def add(chunk_text, section, subsection=None):
        prefix = f"[{source} | {section}" + (f" > {subsection}" if subsection else "") + "] "
        chunks.append({
            "text": prefix + chunk_text.strip(),
            "metadata": {"source": source, "section": section, "subsection": subsection}
        })

    overview_match = re.search(r"^(.*?)General Information", text, re.DOTALL)
    if overview_match:
        add(re.sub(r"\s+", " ", overview_match.group(1)), "Overview")

    gi_match = re.search(r"General Information\n(.*?)\nOperating Hours", text, re.DOTALL)
    if gi_match:
        lines = [l.strip() for l in gi_match.group(1).split("\n") if l.strip()]
        pairs = [f"{lines[i]}: {lines[i+1]}" for i in range(0, len(lines) - 1, 2)]
        add(". ".join(pairs), "General Information")

    hours_match = re.search(r"Operating Hours\nDay\nHours\n(.*?)\nMenu", text, re.DOTALL)
    if hours_match:
        lines = [l.strip() for l in hours_match.group(1).split("\n") if l.strip()]
        pairs = [f"{lines[i]}: {lines[i+1]}" for i in range(0, len(lines) - 1, 2)]
        add(". ".join(pairs), "Operating Hours")

    menu_match = re.search(r"Menu\n(.*?)Reservations & Policies", text, re.DOTALL)
    known_subsections = {"Appetizers", "Soups", "Main Courses", "Vegetarian Options", "Desserts", "Beverages"}
    if menu_match:
        lines = [l.strip() for l in menu_match.group(1).split("\n") if l.strip()]
        current_sub, i = None, 0
        while i < len(lines):
            line = lines[i]
            if line in known_subsections:
                current_sub = line
                i += 1
                continue
            item_match = re.match(r"^(.+?)\s+PHP\s+([\d,]+(?:\s*-\s*[\d,]+)?)$", line)
            if item_match and i + 1 < len(lines):
                name, price = item_match.groups()
                desc_lines, j = [], i + 1
                while j < len(lines) and lines[j] not in known_subsections and not re.match(r"^.+?\s+PHP\s+[\d,]", lines[j]):
                    desc_lines.append(lines[j])
                    j += 1
                add(f"{name.strip()} — PHP {price}. {' '.join(desc_lines)}", "Menu", current_sub)
                i = j
                continue
            i += 1

    policy_match = re.search(r"Reservations & Policies\n(.*?)\nFrequently Asked Questions", text, re.DOTALL)
    if policy_match:
        add(re.sub(r"\s+", " ", policy_match.group(1)), "Policies")

    faq_match = re.search(r"Frequently Asked Questions\n(.*?)This document is a sample", text, re.DOTALL)
    if faq_match:
        pairs = re.findall(r"Q:\s*(.+?)\nA:\s*(.+?)(?=\nQ:|\Z)", faq_match.group(1), re.DOTALL)
        for q, a in pairs:
            add(f"Q: {re.sub(r'\\s+', ' ', q)} A: {re.sub(r'\\s+', ' ', a)}", "FAQ")

    return chunks
