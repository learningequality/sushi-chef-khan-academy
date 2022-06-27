import csv
from io import StringIO

from constants import COMMON_CORE_SPREADSHEET
from network import make_request


CC_MAPPING = {}  # Common Core State Standards slug -> list(tag) to apply


def generate_common_core_mapping():

    resp = make_request(COMMON_CORE_SPREADSHEET, timeout=120)
    csv_data = resp.content.decode("utf-8")

    # This CSV file is in standard format: separated by ",", quoted by '"'
    reader = csv.reader(StringIO(csv_data))
    header_row = []

    # Loop through each row in the spreadsheet.
    for row in reader:

        if row[0] == "Grade":
            # Read the header row.
            header_row = [v.lower() for v in row]  # lcase all header row values
            grade_idx = header_row.index("grade")
            common_core_idx = header_row.index("common core area")
            standard_idx = header_row.index("standard")
            skill_name_idx = header_row.index("name of skill on khan academy")
            link_idx = header_row.index("link to skill")
            description_idx = header_row.index("description")
            area_idx = header_row.index("area")
        else:
            # Grab CC standard and link to exercise
            standard_tag = row[standard_idx]
            link = row[link_idx]
            if not link or not standard_tag:
                continue

            # parse out slug from link and set standard tag
            slug = link.split("e/")[1]
            CC_MAPPING[slug] = standard_tag
