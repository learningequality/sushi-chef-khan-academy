# Khan Academy Sushi Chef

Content integration script for the Khan Academy channels from https://khanacademy.org.


### Step 0: Installation

* [Install pip](https://pypi.python.org/pypi/pip) if you don't have it already.
* [Install Python3](https://www.python.org/downloads) if you don't have it already
* [Install Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) if you don't have it already
* Open a terminal
* Clone this repo, `cd` into it
* Create a Python3 virtual env `virtualenv -p python3  venv`
  and activate it using `source venv/bin/activate`
* Run `pip install -r requirements.txt`


### Step 1: Obtaining an Authorization Token

You will need an authorization token to create a channel on Kolibri Studio. In order to obtain one:

1. Create an account on [Kolibri Studio](https://contentworkshop.learningequality.org/).
2. Navigate to the Tokens tab under your Settings page.
3. Copy the given authorization token (you will need this for later).


### Step 2: Running the chef

Running the KA sushi chef script requires loading some environment variables,
and a single command:

```bash
source venv/bin/activate

source credentials/proxy_list.env
source credentials/crowdinkeys.env

./sushichef.py --reset --token=<token> --thumbnails lang=<lang_code>
```
You'll need to replace `<token>` with your Studio access token obtained earlier
and `<lang_code>` with a le_utils code for the channel (e.g. `en`, `es`, `pt-BR`, etc.).
When running the KA chef command on a remote server, use `nohup ... &` so that
the long-running chef process will not exit when you "hang up" the ssh sesssion.





# Implementation Overview

We use Khan Academy TSV export data to get a tree structure of the language,
which includes topics, videos, and exercises. We map each of these content kinds
to our KhanNode objects, which then get mapped to the ricecooker data structures:

    KA TSV exports --(A)--> KhanNode tree --(B)--> ContentNode tree

During the processing step (A) slug-based filtering is applied to skip certain
nodes (due to technical or licensing limitations). During processing step (B)
the topic tree returned by the KA API is restructured to take advantage of LTTs
see `SLUG_BLACKLIST` and `TOPIC_TREE_REPLACMENTS_PER_LANG` in [`curation.py`](./curation.py).


## Code

### Important chef code

    sushichef.py          Main code for the content integration script
    tsvkhan.py            Functions for loading data from the new KA TSV exports
    constants.py          Constants, metadata, and settings used in the code
    curation.py           Topic node replacements to organize the KA topic trees
    crowdin.py            Obtain translations from CrowdIn
    common_core_tags.py   Helper class to obtain the CCSSM tags for KA exercises
    network.py            Robust HTTP requests that use caching

### Debugging and reports code

    graphql.py            Helper method to extract localized topic trees form the KA website
    katrees.py            Generate report and print topic tree from the KA API
    kolibridb.py          Generate report and print topic tree from Kolibri DBs

Each of these scripts can be called as standalone command line scripts.

**Example 1.** Get localized topic tree info from Khan Academy website:

    ./graphql.py --lang hi   # check the topics structure used on hi.khanacademy.org
    ./graphql.py --lang en --curriculum us-cc   # topic structure for us-cc variant

Use the output of this script to add or update the info in `curaiton.py`.


**Example 2.** Print the entire topic tree from the French TSV export (up to 3 levels)
and also save the tree as an HTML file:

    ./katrees.py --print --printmaxlevel=3 --htmlexport --htmlmaxlevel=4   --lang fr

**Example 3.** Print the topic tree for the currently published Kolibri channel 
Khan Academy (Français) which has channle ID `878ec2e6f88c5c268b1be6f202833cd4`:

    ./kolibridb.py --channel_id 878ec2e6f88c5c268b1be6f202833cd4 --printmaxlevel 3 --update

The output is similar to tree output of **Example 2** so it can be used for comparing
and debugging (what we get from the TSV exports vs. what the final channel produced).


**Example 4.** The code in `tsvkhan.py` is also runnable as a standalone script:
  
    ./tsvkhan.py   # list the available TSV exports for all languages
    ./tsvkhan.py --kalang fr     # list the TSV exports available for French

### KhanExercise

Each exercise has a list of assessment item IDs associated with it. In order to retrieve each
assessment item we use, `https://www.khanacademy.org/api/v1/assessment_items/{id}?lang={lang}`.
We only include the assessment item if the content is fully translated by looking
at `is_fully_translated` from the response.


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
content in English was originally organized around high-level Subjects.
Later, an additional "Math by grade" topic structure was added that contains the
same videos and lessons but organized according to the US Common Core Math standards.
Certain KA languages offer an additional topic structures aligned to local grade levels
called Localized Topic Trees (LTTs). The KA website offers multiple top-level menu
topics that can vary with both language and region. All the topic trees are available
through the KA API, but the different topic trees co-exist within the same tree
structure as returned by the KA API, which can be overwhelming for users since
the same content appears repeatedly and organization is unexpected.

The `SLUG_BLACKLIST` and `TOPIC_TREE_REPLACMENTS_PER_LANG` info in `curation.py`
allows us to take advantage of these multiple topics trees and present Kolibri
users with a topic tree structure that closely resemble the Khan Academy website.
Each Kolibri channel is created with a combination of (`lang`,`variant`) where
lang is one of the `le_utils` language codes, and variant is one of the "curriculum"
variants available for that language. For example, the Khan Academy English content
comes in two variants, the US variant (`us-cc`) and the India variant (`in-in`).
Here is a complete list of channels and command line options lang/variant for them:

- Arabic: youtube playlist channel via https://www.youtube.com/user/KhanAcademyArabi/playlists
  See also https://ar.khanacademy.org/
- Bengali: `lang=bn` https://bn.khanacademy.org/
- Bulgarian: `lang=bg` https://bg.khanacademy.org/
- German: `lang=de` https://de.khanacademy.org/
- English: `lang=en` https://www.khanacademy.org/ comes in three variants:
  - Khan Academy (English - US curriculum): `lang=en`, `variant=us-cc` is based
    on the menu of https://www.khanacademy.org/?curriculum=us-cc and including
    "Math by subject" and "Math by grade" hierarchies aligned to the US common core.
  - Khan Academy (English - India curriculum): `lang=en`, `variant=in-in` which
    is based on the topic tree for the Indian curriculum https://www.khanacademy.org/?curriculum=in-in
- Spanish: `lang=es`: the default Spanish content from https://es.khanacademy.org/
  that also includes the Mexico-aligned math "Matemáticas por grado (México)"
  taken from https://es.khanacademy.org/?curriculum=mx-eb and 
  "Matemáticas por grado (Perú)" taken from https://es.khanacademy.org/?curriculum=pe-pe
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
