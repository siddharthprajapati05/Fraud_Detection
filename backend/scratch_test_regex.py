import re

PATTERNS = {
    "name": r"(?:Name|NAME)[:\s]+([A-Z][a-zA-Z\s]{2,40})",
}

text1 = "Name: SIDDHARTH PRAJAPATI\nDOB: 01/01/1990"
text2 = "Name \n SIDDHARTH PRAJAPATI\n"
text3 = "Nam: SIDDHARTH PRAJAPATI\n"
text4 = "Name : Siddharth Prajapati\n"

for i, t in enumerate([text1, text2, text3, text4]):
    m = re.search(PATTERNS["name"], t, re.IGNORECASE)
    if m:
        print(f"Text {i+1}: MATCH -> {m.group(1).strip()}")
    else:
        print(f"Text {i+1}: NO MATCH")
