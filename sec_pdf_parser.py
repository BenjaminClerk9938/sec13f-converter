import fitz  # PyMuPDF
import re
import pandas as pd


def extract_sec_data(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        full_text += page.get_text() + "  "
    # Here you would need to parse and format the text to extract relevant fields like CUSIP
    sec_data = process_extracted_text(full_text)
    # print(sec_data)
    return sec_data


def process_extracted_text(text):
    lines = text.split("\n")
    lines = [line for line in lines if line.strip()]
    lines = [
        line
        for line in lines
        if len(line) >= 3
        and not (
            "**" in line or "CUSIP" in line or "ISSUER" in line or "STATUS" in line
        )
    ]
    cnt = 0
    data_array = []
    flag = False
    entry = None
    regex = re.compile(r"\b[A-Z0-9]{6} \b[A-Z0-9]{2} \d{1}\b")

    for line in lines:
        if regex.search(line):
            if entry:
                data_array.append(entry)
            entry = {
                "cusip_no": re.sub(r"\s+", "", line),
                "issuer_name": "",
                "issuer_description": "",
                "status": "",
            }
            cnt = 0
            flag = True
        elif flag:
            cnt += 1
            if cnt == 1:
                entry["issuer_name"] = line
            elif cnt == 2:
                entry["issuer_description"] = line
            elif cnt == 3:
                status_match = re.search(r"(ADDED|DELETED)", line)
                entry["status"] = status_match.group(0) if status_match else ""

    # Append the last entry
    if entry:
        data_array.append(entry)

    # Combine the data
    result_array = []
    temp_obj = {}

    df = pd.DataFrame(data_array)
    df.to_excel("sec_data.xlsx", index=False)

    for item in data_array:
        # Merge the current item into the temporary object
        temp_obj.update(item)
        # When we find a `cusip_no`, we consider the group complete
        if item["cusip_no"]:
            result_array.append(temp_obj)
            temp_obj = {}  #
    return result_array
