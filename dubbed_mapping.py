import csv
from io import StringIO

from constants import KA_LITE_DUBBED_LIST
from network import make_request


def generate_dubbed_video_mappings_from_csv():

    resp = make_request(KA_LITE_DUBBED_LIST, timeout=120)
    csv_data = resp.content.decode("utf-8")

    # This CSV file is in standard format: separated by ",", quoted by '"'
    reader = csv.reader(StringIO(csv_data))
    video_map = {}
    header_row = []

    # Loop through each row in the spreadsheet.
    for row in reader:
        # skip over the header rows
        if row[0].strip() in ["", "UPDATED:"]:
            continue

        elif row[0] == "SERIAL":
            # Read the header row.
            header_row = [v.lower() for v in row]  # lcase all header row values (including language names)
            slug_idx = header_row.index("title id")
            english_idx = header_row.index("english")
            assert slug_idx != -1, "Video slug column header should be found."
            assert english_idx != -1, "English video column header should be found."

        else:
            # Rows 6 and beyond are data.
            assert len(row) == len(header_row), "Values line length equals headers line length"

            # Grab the slug and english video ID.
            video_slug = row[slug_idx]
            english_video_id = row[english_idx]
            assert english_video_id, "English Video ID should not be empty"
            assert video_slug, "Slug should not be empty"

            # English video is the first video ID column,
            #   and following columns (until the end) are other languages.
            # Loop through those columns and, if a video exists,
            #   add it to the dictionary.
            for idx in range(english_idx, len(row)):
                if not row[idx]:  # make sure there's a dubbed video
                    continue

                lang = header_row[idx]
                if lang not in video_map:  # add the first level if it doesn't exist
                    video_map[lang] = {}
                dubbed_youtube_id = row[idx]
                if english_video_id == dubbed_youtube_id and lang != "english":
                    print("Removing entry for (%s, %s): dubbed and english youtube ID are the same." % (lang, english_video_id))
                else:
                    video_map[lang][english_video_id] = row[idx]  # add the corresponding video id for the video, in this language.
    return video_map
