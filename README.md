# Khan Academy Sushi Chef

Sushi Chef for khanacademy.org

### Step 0: Installation

* [Install pip](https://pypi.python.org/pypi/pip) if you don't have it already.
* [Install Python3](https://www.python.org/downloads) if you don't have it already
* [Install Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) if you don't have it already
* Open a terminal
* Clone this repo, `cd` into it
* Create a Python3 virtual env `virtualenv -p python3  venv`
  and activate it using `source venv/bin/activate`
* Run `pip install -r requirements.txt`

### Step 1: Obtaining an Authorization Token ###
You will need an authorization token to create a channel on Kolibri Studio. In order to obtain one:

1. Create an account on [Kolibri Studio](https://contentworkshop.learningequality.org/).
2. Navigate to the Tokens tab under your Settings page.
3. Copy the given authorization token (you will need this for later).

### Step 2: Running the chef ###
Run `./json_chef.py --reset --token=<token> --thumbnails lang=<lang_code>`,
replacing `<token>` with the token you copied earlier and `<lang_code>` with a 
le-utils language code for one of the Khan Academy lanugages. (ex. '**en**')

<!--
 * Supported Language Codes: en, es, pt-BR, pt-PT, fr, sw
 * Lite Language Codes: zu
-->

# Implementation Overview

We use `https://www.khanacademy.org/api/v2/topics/topictree?lang={lang}&projection=<projection>`,
to get a tree structure of the language, which includes topics, videos, and exercises.
Using the `projection` attribute we can pass in the specific attributes for each 
content kind such as `projection={"topics": [{"translatedTitle": 1}], "exercises": [{"id": 1, "name": 1}], "videos": [{"id": 1,"youtubeId": 1}]}`
(Note: These are only a subset of the attributes we pass in. For a full list see,
https://github.com/learningequality/sushi-chef-khan-academy/blob/master/constants.py).

We map each of these content kinds to our KhanNode objects, which then get mapped
to the ricecooker data structures:

    KA API json data --(A)--> KhanNode tree --(B)--> ContentNode tree

During the processing step (A) slug-based filtering is applied to skip certain
nodes (due to technical or licensing limitiations). During processing step (B)
the topic tree returned by the KA API is restructured to take advantage of LTTs
see `SLUG_BLACKLIST` and `TOPIC_TREE_REPLACMENTS_PER_LANG` in [`curation.py`](./curation.py).





### KhanExercise

Each exercise has a list of assessment item IDs associated with it. In order to retrieve each assessment item we use, `https://www.khanacademy.org/api/v1/assessment_items/{id}?lang={lang}`. We only include the assessment item if the content is fully translated by looking at `is_fully_translated` from the response.

### Data Mapping
Below is a table which shows the mapping from the Khan data structures to the Ricecooker data structures.

| KA Data Structures    | Ricecooker Data Structures  |
| ------------------    | --------------------------  |
| `KhanTopic`           | `nodes.TopicNode`           |
| `KhanExercise`        | `nodes.ExerciseNode`        |
| `KhanAsessmentItem`   | `questions.PerseusQuestion` |
| `KhanVideo`           | `nodes.VideoNode`           |
| `KhanArticle`         | Not Supported               |
| `KhanScratchpad`      | Not Supported               |


### TODOs
 - Handle `prerequisites` (links to exercises slugs)
 - Handle `relatedContent` (links to videos, exercises, and scratchpads on the same concept)
 - Investigate private videos in zh-CN, e.g.
   https://zh.khanacademy.org/math/basic-geo/basic-geo-angle#angles-between-lines
   and https://zh.khanacademy.org/economics-finance-domain/core-finance/money-and-banking



## Channel variants and Localized Topic Trees (LTTs)
The Khan Academy content is available under different topic structures. The KA
content in English was originally organized around high-level Subjects. Later,
an additional "Math by grade" topic structure was added that contains the same
videos and lessons but organized according to the US Common Core Math standards.
Certain KA languages offer an additional topic structure aligned to local grade
levels and curriculula called Localized Topic Trees (LTTs). The KA website offers
multiple top-level menu topics that can vary with both language and region.
All the topic trees are available through the KA API, but the different topic
trees co-exist within the same tree structure as returned by the KA API, which
can be overwhelming for users (same repeated content and unepected organization).

The `SLUG_BLACKLIST` and `TOPIC_TREE_FOR_LANG_AND_VARIANT` info in `curation.py`
allows us to take advantage of these multiple topics trees and present Kolibri
users with a topic tree structure that closely resmeble the Khan Academy website.
Each Kolibri channel is created with a combination of (`lang`,`variant`) where
lang is one of the le-utils language codes, and variant is one of the "curriculum"
variants available for that language. For example, the Khan Academy English content
comes in two variants, the "default" variant (`None`) and the India variant (`in-in`).
Here is a complete list of channels and command line options lang/variant for them:

- Arabic: youtube playlist channel via https://www.youtube.com/user/KhanAcademyArabi/playlists
  See also https://ar.khanacademy.org/
- Bengali: `lang=bn` https://bn.khanacademy.org/
- Bulgarian: `lang=bg` https://bg.khanacademy.org/
- German: `lang=de` https://de.khanacademy.org/
- English: `lang=en`
  - Khan Academy (English): `lang=en`, `variant=None`. This is the regular topic
    tree including "Math by subject" and "Math by grade" hierarchies, but not
    the the `in-in` topics. Should be similar to https://www.khanacademy.org/
- Khan Academy (English - India): `lang=en`, `variant=in-in` which is based on the
  topic tree for the Indian curriculum https://www.khanacademy.org/?curriculum=in-in
- Spanish: `lang=es`: the default Spanish content from https://es.khanacademy.org/
  that also includes the Mexico-aligned math "Matemáticas por grado (México)"
  taken from https://es.khanacademy.org/?curriculum=mx-eb
- Français: `lang=fr` channel that combines the topic both French and Belgian topic trees
  - Maths accès par classe (France): https://fr.khanacademy.org/?curriculum=fr-fr
  - Maths accès par classe (Belgique): https://fr.khanacademy.org/?curriculum=be-be
- Fulfulde Mbororo: `lang=ful` special math exercises only channel generated by
  `fv_json_chef.py` (as requested by partner). Note language code on CrowdIn is `fv`
- Gujarari: `lang=gu` https://gu.khanacademy.org/
  Two channels exist 5357e52581c3567da4f56d56badfeac7 (??) and 216f46094b8644d5b80c18285f5224ff (public)
- Hindi: `lang=hi` https://hi.khanacademy.org/
  Note there is more Hindi content in English - India channel (lang=en, variant=in-in),
  with the main differnece being that the topic titles are translated in this channel
- Armenian: `lang=hy` https://hy.khanacademy.org/
- Indonesian: `lang=id` https://id.khanacademy.org/
- Italian: `lang=it` https://it.khanacademy.org/
- Korean: `lang=ko` https://ko.khanacademy.org/
- Burmese: `lang=my` https://my.khanacademy.org/
- Brazil Portuguese: `lang=pt-BR`
  Topic tree base don https://pt.khanacademy.org/ <=302= https://pt-br.khanacademy.org/
- Portugal Portuguese: `lang=pt-BR`
  Topic tree based on: https://pt-pt.khanacademy.org/
- Russian: `lang=ru` currently get ferom https://www.youtube.com/user/KhanAcademyRussian/playlists
  but https://ru.khanacademy.org/ is also available
- Swahili: `lang=sw` https://sw.khanacademy.org/
  https://www.youtube.com/user/KhanAcademyKiswahili/playlists
  Special chef that incluses also English videos
- Chinese: `lang=zh-CN` https://zh.khanacademy.org/
- isiZulu: `lang=zul` https://zu.khanacademy.org/
  see also https://www.youtube.com/user/KhanAcademyZulu/playlists
