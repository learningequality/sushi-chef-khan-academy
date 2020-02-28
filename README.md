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
Run `./json_chef.py -v --reset --token=<token> --stage --thumbnails lang=<lang_code>`, replacing `<token>` with the token you copied earlier and `<lang_code>` with a Khan Academy supported language code. (ex. '**en**')

<!--
 * Supported Language Codes: en, es, pt-PT, fr, sw
 * Lite Language Codes: zu
-->

# Implementation Overview

We use `https://www.khanacademy.org/api/v2/topics/topictree?lang={lang}&projection=<projection>`, in order to get a tree structure of a specific language, which includes topics, videos, and exercises. We map each of these content kinds to our Khan data structures, which then get mapped to the ricecooker data structures. 
Using the `projection` attribute we can pass in the specific attributes for each content kind such as `projection={"topics": [{"translatedTitle": 1}], "exercises": [{"id": 1, "name": 1}], "videos": [{"id": 1,"youtubeId": 1}]}` (Note: These are only a subset of the attributes we pass in. For a full list see, https://github.com/learningequality/sushi-chef-khan-academy/blob/master/constants.py).

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
 - Respect topics with `doNotPublish` set to `true` in JSON.
 - Handle `prerequisites` (links to exercises slugs)
 - Handle `relatedContent` (links to videos, exercises, and scratchpads on the same concept)
 - Update to use standard `config.LOGGER` for logging



