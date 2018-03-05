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
Run `./chef.py -v --reset --token=<token> --stage --thumbnails lang=<lang_code>`, replacing `<token>` with the token you copied earlier and `<lang_code>` with a Khan Academy supported language code. (ex. '**en**')

<!--
 * Supported Language Codes: en, es, pt-PT, fr, sw
 * Lite Language Codes: zu
-->

