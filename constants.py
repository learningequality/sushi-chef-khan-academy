from le_utils.constants.languages import getlang
from ricecooker.classes.licenses import CC_BYLicense
from ricecooker.classes.licenses import CC_BY_NCLicense
from ricecooker.classes.licenses import CC_BY_NC_NDLicense
from ricecooker.classes.licenses import CC_BY_NC_SALicense
from ricecooker.classes.licenses import CC_BY_SALicense
from ricecooker.classes.licenses import SpecialPermissionsLicense

# These KA channels are not fully supported on the KA website, but content may
# be available as YouTube playlists and via exercise translations from Crowdin.
UNSUPPORTED_LANGS = [
    "zul",  # note KA kalang is `zu`
    "ur",
]


CROWDIN_URL = "https://api.crowdin.com/api/project/khanacademy/download/{lang_code}.zip?login={username}&account-key={account_key}"
COMMON_CORE_SPREADSHEET = (
    "https://storage.googleapis.com/ka_uploads/share/Common_Core_Spreadsheet.csv"
)


# Videos with misleading translatedYoutubeLang organized by le-utils lang code.
# Use this list to override the should-be-included logic and include the videos.
# TODO: read the `sourceLanguage` property from the future KA API insead of list
DUBBED_VIDEOS_BY_LANG = {
    "pt-BR": [
        "UnPpFw3natI",
        "LYUmHD__MRg",
        "N8qRX_7po9U",
        "VjhbocJYyOI",
        "awyS59G8uZA",
        "DfBjGvdUMVM",
        "39m4SSfP2Y0",
        "rsoMED7zHME",
        "fFRvZI0K4wQ",
        "mO4senTBFbc",
        "uikYPJw0tnE",
        "50q4iKwnLe8",
        "R--9PJ355jY",
        "CPhXo-7Qilk",
        "TSZ4H5Hd9-M",
        "VdIlzUigamE",
        "dGZTQxyfwPI",
        "9HZz32sBAvA",
        "pliaCSX-B4I",
        "NSZ8oGkfO14",
        "5rkJ4Ve_2gc",
        "iheXqmtLhts",
        "WzHBBfxl6zo",
        "19G_f9oHIeg",
        "Bvq4pfmP03s",
        "7sp1--UsVoY",
        "eviU0iRKcck",
        "v_joLaJ-cfM",
        "kfikcE4eJMI",
        "9_o8Lw9BU_U",
        "N0IO9b-xnzc",
        "GCTea37THw0",
        "FllpnWMCeCw",
        "seR3m7RNRRA",
        "QM13R2YhyD0",
        "P4n36FnlQ18",
        "5j7QWssTZTM",
        "C7Uw4g8GCkU",
        "Y3qLdwRY5RY",
        "rp1E8idtvJY",
        "bDxYr6LWL5A",
        "v1RBFkoLD0w",
        "L2Z-1EeXAjo",
        "x5j19Dd5jWU",
        "OLkz5WfQHG4",
        "cQT8ZZAbrow",
        "XCaw6TxgLoQ",
        "Z7nh2e5dVYE",
        "eQNhW0t_R-k",
        "q1-7lYXirHs",
        "296y0W2lu4w",
        "3dOVJCtN1kE",
        "Qne5wRW20VA",
        "dTsUyXXudvA",
        "Iya-2bS14ho",
        "bm65xCS5ivo",
        "oW8Ts9N5E-o",
        "ENc3fmAQG5Q",
        "a4o-3vvTOkU",
        "o9e7U1IQ7Ek",
        "1jJBfzVQ-qQ",
        "jnyOVKseNNw",
        "Z3xs9saGdTQ",
        "sSNu75F5JeQ",
        "TXHr1h356Ps",
        "BWjWEDvTB7g",
        "B8HhdnIhAVg",
        "wXQ3vPrKer0",
        "XZ9Zw9_cTII",
        "r2mm0vTjD3k",
        "B-vlVXbS_4Y",
        "Qz2-5pi1PcM",
        "0uPgRLUAiuU",
        "J8Pvc6JB5ts",
        "W6w5S-bAmwM",
        "yRh_Pah7AHo",
        "qlGjA9p1UAM",
        "36Xv2JyPyqA",
        "OKc64ezg1uU",
        "vPj9S6XsLUM",
        "AmUiEjPEaiM",
        "lrnXQXCLpAQ",
        "Qite1chTX2s",
        "ngQ_luLpeWI",
        "BnxcORk2tLc",
        "X4MaFYJUYYk",
        "e3H_nqrPuUQ",
        "kTgKXsA_klo",
        "g6NEzuwZ-0Q",
        "FqxyxAq4OMU",
        "Z4sirIWw3Lk",
        "7AQ3rUb3gWg",
        "gYHUrpmB-L4",
        "h1bG6zy8ENY",
        "5MOn8X-tyFw",
        "7JuoW8Pz7gU",
        "qtbb4YBJbJM",
        "2HZKYXXyHJQ",
        "8BBcQ67myf0",
        "NUG1JzxL7jw",
        "e7Cf9eepOTQ",
        "o4bXSA7vrd8",
        "bsIzwvKHZPc",
        "xx8w1WStqpg",
        "Om5nvig9Ahs",
        "tO6UMCo8LVU",
        "4YB_zVM23XA",
        "lZiEcMJaw5c",
        "oJ4PhVSkEzg",
        "LnA0NhBB7pk",
        "50f8X_52O-E",
        "YXL6IFa1TJg",
        "DJVJQAgXsGg",
        "2B4A4kigi4Q",
        "kXSyFWk_0T4",
        "oeAvj4P6S8o",
        "EOPbuL73G4s",
        "T2hO0qO3qLc",
        "-J41zkn-HlU",
        "l4oStl_JYlU",
        "U5vAO_f2LDQ",
        "9REQTbtrwpc",
        "m0tdMIz_UHA",
        "Qd2n_vZdXuA",
        "Z5GoBku8hUo",
        "MyEFnkuxViU",
        "eRN2gy-Je18",
        "c2-kabi2_ao",
        "FS3FSxG_Am0",
        "h2NKJK8wjU0",
        "KpK5GVXtF8g",
        "YhzH8iVMHl0",
        "1XlW-7WdHfA",
        "1U6Aqc0U3OM",
        "GMLP5jOnqAI",
        "tYP_e2IitEA",
        "JVOU_sh0qpA",
        "z7hVq6OdwOg",
        "BTudzgYleUI",
        "CYJ5sq8AZFI",
        "JeuaB4iryqU",
        "H51OAPifRiw",
        "TPqE9qP7aHU",
        "J2reLNBqoK0",
        "HkZ7y05ycEo",
        "_1RUYZ8Ic0E",
        "1l2yttNDYtc",
        "402Irx3SMRc",
    ]
}
# To add to this list, look for ERROR message in the logs after a complete chef
# like "Untranslated video {youtube_id} and no subs available. Skipping." and
# add the `{youtube_id}` to the above list if the video is actually transalted.


LICENSE_MAPPING = {
    # OLD KEYS
    "CC BY": CC_BYLicense(copyright_holder="Khan Academy"),
    "CC BY-NC": CC_BY_NCLicense(copyright_holder="Khan Academy"),
    "CC BY-NC-ND": CC_BY_NC_NDLicense(copyright_holder="Khan Academy"),
    "CC BY-NC-SA (KA default)": CC_BY_NC_SALicense(copyright_holder="Khan Academy"),
    "CC BY-SA": CC_BY_SALicense(copyright_holder="Khan Academy"),
    "Non-commercial/non-Creative Commons (College Board)": SpecialPermissionsLicense(
        copyright_holder="Khan Academy",
        description="Non-commercial/non-Creative Commons (College Board)",
    ),
    # "Standard Youtube": licenses.ALL_RIGHTS_RESERVED,  # warn and skip these
    #
    #
    #
    # NEW KEYS
    "cc-by-nc-nd": CC_BY_NC_NDLicense(copyright_holder="Khan Academy"),
    "cc-by-nc-sa": CC_BY_NC_SALicense(copyright_holder="Khan Academy"),
    "cb-ka-copyright": SpecialPermissionsLicense(
        copyright_holder="Khan Academy",
        description="Non-commercial/non-Creative Commons (College Board)",
    ),
    # 'yt-standard': licenses.ALL_RIGHTS_RESERVED,  # warn and skip these
}


# BEGIN AUTO-GENERATED LANGUAGE_CURRICULUM_MAP
# This section is auto-generated by analyze_tsv_languages.py
# Do not manually edit between BEGIN and END markers
#
# Auto-generated comprehensive language and curriculum lookup
# This constant consolidates information from Khan Academy TSV exports
# and replaces SUPPORTED_LANGS, CHANNEL_TITLE_LOOKUP, and CHANNEL_DESCRIPTION_LOOKUP
#
# Each language entry contains:
#   - ka_lang: Khan Academy language code
#   - le_lang: le-utils language code
#   - name: English name of the language
#   - native_name: Native name of the language
#   - curricula: Optional list of curriculum variants (if any)
#   - title: Channel title (if no curricula)
#   - description: Channel description (if no curricula)
LANGUAGE_CURRICULUM_MAP = [
    {
        "ka_lang": "ar",
        "le_lang": "ar",
        "name": "Arabic",
        "native_name": "العربية",
        "title": "Khan Academy (العربية)",
        "description": "Khan Academy content for Arabic.",
    },
    {
        "ka_lang": "as",
        "le_lang": "as",
        "name": "Assamese",
        "native_name": "অসমীয়া",
        "title": "Khan Academy (অসমীয়া)",
        "description": "Khan Academy content for Assamese.",
    },
    {
        "ka_lang": "az",
        "le_lang": "az",
        "name": "Azerbaijani",
        "native_name": "azərbaycan dili",
        "title": "Khan Academy (azərbaycan dili)",
        "description": "Khan Academy tələbələrə istənilən vaxt tapşırıqların üzərində işləmək, təlimat videolarını izləmək və fərdiləşdirilmiş öyrənmə paneli ilə həm sinifdə, həm də sinifdən kənar təhsil almaq imkanı verir. Khan Academy-də uşaq bağçasından başlayaraq ali təhsil daxil olmaqla müxtəlif fənləri, o cümlədən riyaziyyat, həyat bilgisi, oxu, hesablama, tarix, incəsənət tarixi, iqtisadiyyat, maliyyə savadlılığı, SAT, MCAT və digər sahələri əhatə edən tədris resursları yer alır. Beləliklə, təhsilalanların məktəbdə, ali təhsildə və peşəkar fəaliyyətdə lazım olan təməl biliklərin əldə olunması üçün imkanlar yaradır.",
    },
    {
        "ka_lang": "bg",
        "le_lang": "bg",
        "name": "Bulgarian",
        "native_name": "български език",
        "title": "Khan Academy (български език)",
        "description": "Khan Academy предоставя видео уроци и упражнения по математика, физика, химия и биология, съобразени с българските учебни стандарти. Темите са представени чрез лесно разбираеми обяснения и многобройни упражнения за самооценка на наученото. Материалите са подходящи както за ученици от началните и стредните класове, така и за студенти.",
    },
    {
        "ka_lang": "bn",
        "le_lang": "bn",
        "name": "Bengali",
        "native_name": "বাংলা",
        "title": "Khan Academy (বাংলা)",
        "description": "খান একাডেমিতে বাংলাদেশের শিক্ষাক্রম অনুযায়ী গণিতের ভিডিও এবং অনুশীলনী রয়েছে। প্রতিটি অধ্যায়ে বিষয়ভিত্তিক মূল ধারণার ভিডিও এবং অসংখ্য অনুশীলনী রয়েছে যা নিয়মিত চর্চার মাধ্যমে শিক্ষার্থীরা ঐ বিষয়ে দক্ষতা অর্জন করতে পারে। প্রাথমিক ও মাধ্যমিক শিক্ষার্থীদের জন্য উপযোগী, সেইসাথে বয়স্ক শিক্ষার্থীরাও এটি ব্যবহার করতে পারবে।",
    },
    {
        "ka_lang": "cs",
        "le_lang": "cs",
        "name": "Czech",
        "native_name": "česky, čeština",
        "title": "Khan Academy (česky)",
        "description": "Khan Academy content for Czech.",
    },
    {
        "ka_lang": "da",
        "le_lang": "da",
        "name": "Danish",
        "native_name": "Dansk",
        "title": "Khan Academy (Dansk)",
        "description": "Khan Academy content for Danish.",
    },
    {
        "ka_lang": "de",
        "le_lang": "de",
        "name": "German",
        "native_name": "Deutsch",
        "title": "Khan Academy (Deutsch)",
        "description": "Khan Academy content for German.",
    },
    {
        "ka_lang": "el",
        "le_lang": "el",
        "name": "Greek, Modern",
        "native_name": "Ελληνικά",
        "title": "Khan Academy (Ελληνικά)",
        "description": "Khan Academy content for Greek, Modern.",
    },
    {
        "ka_lang": "en",
        "le_lang": "en",
        "name": "English",
        "native_name": "English",
        "curricula": [
            {
                "curriculum_key": "ca-ab",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "ca-on",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "in-in",
                "title": "Khan Academy (English - CBSE India Curriculum)",
                "description": "Khan Academy provides videos and exercises on math, physics, chemistry, biology, and history, aligned to the CBSE India curriculum. Each topic is covered through intuitive video explanations and provides numerous practice exercises to help students achieve mastery of the subjects. Appropriate for middle and secondary students, as well as adult learners.",
            },
            {
                "curriculum_key": "ke-ke",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "ph-ph",
                "title": "Khan Academy (English - Philippines Curriculum)",
                "description": "",
            },
            {
                "curriculum_key": "pk-pk",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "sl-sl",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "us-cc",
                "title": "Khan Academy (English - US curriculum)",
                "description": "Khan Academy provides videos and exercises on math, physics, chemistry, biology, and history, aligned to the U.S. curriculum. Each topic is covered through intuitive video explanations and provides numerous practice exercises to help students achieve mastery of the subjects. Appropriate for middle and secondary students, as well as adult learners.",
            },
            {
                "curriculum_key": "us-fl",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "us-tx",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "us-va",
                "title": "",
                "description": "",
            },
        ],
    },
    {
        "ka_lang": "es",
        "le_lang": "es",
        "name": "Spanish",
        "native_name": "Español",
        "curricula": [
            {
                "curriculum_key": "mx-eb",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "pe-pe",
                "title": "",
                "description": "",
            },
        ],
    },
    {
        "ka_lang": "fr",
        "le_lang": "fr",
        "name": "French",
        "native_name": "Français, langue française",
        "curricula": [
            {
                "curriculum_key": "be-be",
                "title": "",
                "description": "",
            },
            {
                "curriculum_key": "fr-fr",
                "title": "",
                "description": "",
            },
        ],
    },
    {
        "ka_lang": "fv",
        "le_lang": "fuv",
        "name": "Fulfulde Mbororo; Fulfulde Mbororoore",
        "native_name": "Fulfulde",
        "title": "Khan Academy (Fulfulde)",
        "description": "Nder Kaan Akademi, bee Fulfulde, a taway wideyo e kuuɗe ngam ekkitaago lissaafi. Bee ɗemle feere, a foti jannga kemestiri, fisiks, e bayoloji fuu. Kala ekkitinol fuu e woodi wideyo ngam janngingo pukaraajo, bee kuuɗe ɗuɗɗe ɗe pukaraajo huwata ngam ɗiggingo ko mo ekkiti. Ekkitinki kin nafay fukaraaɓe diga fuɗɗoode janngirde haa janngirde suudu 12 e yeeso. Mawɓe maa njanngay.",
    },
    {
        "ka_lang": "gu",
        "le_lang": "gu",
        "name": "Gujarati",
        "native_name": "ગુજરાતી",
        "title": "Khan Academy (ગુજરાતી)",
        "description": "ખાન એકેડેમી ગણિત અને વિજ્ઞાન ના વિડિયો અને સ્વાધ્યાય પ્રદાન કરે છે. દરેક વિષય સાહજિક વિડિયો અને અસંખ્ય સ્વાધ્યાયના સાથે આવરી લેવામાં આવે છે. તેઓ વિષયોને માસ્ટર બનાવવામાં મદદ કરે છે.",
    },
    {
        "ka_lang": "hi",
        "le_lang": "hi",
        "name": "Hindi",
        "native_name": "हिन्दी, हिंदी",
        "title": "Khan Academy (हिन्दी)",
        "description": "खान अकादमी गणित वीडियो और अभ्यास प्रदान करता है। प्रत्येक विषय सहज वीडियो और कई अभ्यासों के साथ कवर किया गया है। वे विषयों में निपुण होने में मदद करते हैं।",
    },
    {
        "ka_lang": "hu",
        "le_lang": "hu",
        "name": "Hungarian",
        "native_name": "Magyar",
        "curricula": [
            {
                "curriculum_key": "uk-nc",
                "title": "",
                "description": "",
            },
        ],
    },
    {
        "ka_lang": "hy",
        "le_lang": "hy",
        "name": "Armenian",
        "native_name": "Հայերեն",
        "title": "Khan Academy (Հայերեն)",
        "description": "Khan Academy content for Armenian.",
    },
    {
        "ka_lang": "id",
        "le_lang": "id",
        "name": "Indonesian",
        "native_name": "Bahasa Indonesia",
        "title": "Khan Academy (Bahasa Indonesia)",
        "description": "Khan Academy content for Indonesian.",
    },
    {
        "ka_lang": "it",
        "le_lang": "it",
        "name": "Italian",
        "native_name": "Italiano",
        "title": "Khan Academy (Italiano)",
        "description": "Khan Academy offre i video e gli esercizi di matematica, allineati al curriculum degli Stati Uniti. Ogni argomento è trattato in modo intuitivo attraverso spiegazioni video, e fornisce numerosi esercizi pratici per aiutare gli studenti raggiungere la competenza sulla materia. Adatto agli studenti di scuola elementare, media e secondaria, nonché agli adulti.",
    },
    {
        "ka_lang": "ja",
        "le_lang": "ja",
        "name": "Japanese",
        "native_name": "日本語 (にほんご／にっぽんご)",
        "title": "Khan Academy (日本語 (にほんご／にっぽんご))",
        "description": "Khan Academy content for Japanese.",
    },
    {
        "ka_lang": "ka",
        "le_lang": "ka",
        "name": "Georgian",
        "native_name": "ქართული",
        "title": "Khan Academy (ქართული)",
        "description": "Khan Academy content for Georgian.",
    },
    {
        "ka_lang": "kk",
        "le_lang": "kk",
        "name": "Kazakh",
        "native_name": "Қазақ тілі",
        "title": "Khan Academy (Қазақ тілі)",
        "description": "Khan Academy content for Kazakh.",
    },
    {
        "ka_lang": "km",
        "le_lang": "km",
        "name": "Khmer",
        "native_name": "ភាសាខ្មែរ",
        "title": "Khan Academy (ភាសាខ្មែរ)",
        "description": "Khan Academy ផ្តល់ជូននូវវីដេអូ និងលំហាត់គណិតវិទ្យាជាច្រើន។ គ្រប់មុខវិជ្ជាទាំងអស់ត្រូវបានផ្សព្វផ្សាយតាមរយៈវីដេអូវិចារណញាណ និងមានលំហាត់ជាច្រើនទៀតដើម្បីជួយឱ្យសិស្សមានគន្លឹះក្នុងការដោះស្រាយលំហាត់កាន់តែងាយស្រួល។",
    },
    {
        "ka_lang": "kn",
        "le_lang": "kn",
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "title": "Khan Academy (ಕನ್ನಡ)",
        "description": "Khan Academy content for Kannada.",
    },
    {
        "ka_lang": "ko",
        "le_lang": "ko",
        "name": "Korean",
        "native_name": "한국어 (韓國語), 조선말 (朝鮮語)",
        "title": "Khan Academy (한국어 (韓國語))",
        "description": "Khan Academy content for Korean.",
    },
    {
        "ka_lang": "ky",
        "le_lang": "ky",
        "name": "Kirghiz; Kyrgyz",
        "native_name": "кыргыз тили",
        "title": "Khan Academy (кыргыз тили)",
        "description": "Khan Academy content for Kirghiz; Kyrgyz.",
    },
    {
        "ka_lang": "lt",
        "le_lang": "lt",
        "name": "Lithuanian",
        "native_name": "lietuvių kalba",
        "title": "Khan Academy (lietuvių kalba)",
        "description": "Khan Academy content for Lithuanian.",
    },
    {
        "ka_lang": "lv",
        "le_lang": "lv",
        "name": "Latvian",
        "native_name": "latviešu valoda",
        "title": "Khan Academy (latviešu valoda)",
        "description": "Khan Academy content for Latvian.",
    },
    {
        "ka_lang": "mn",
        "le_lang": "mn",
        "name": "Mongolian",
        "native_name": "монгол",
        "title": "Khan Academy (монгол)",
        "description": "Khan Academy content for Mongolian.",
    },
    {
        "ka_lang": "mr",
        "le_lang": "mr",
        "name": "Marathi (Marāṭhī)",
        "native_name": "मराठी",
        "title": "Khan Academy (मराठी)",
        "description": "Khan Academy content for Marathi (Marāṭhī).",
    },
    {
        "ka_lang": "my",
        "le_lang": "my",
        "name": "Burmese",
        "native_name": "ဗမာစာ",
        "title": "Khan Academy (ဗမာစာ)",
        "description": "Khan Academy မှဗွီဒီယိုများနှင့်သင်္ချာဆိုင်ရာလေ့ကျင့်ခန်းများကိုတင်ဆက်သည်။ ဘာသာရပ်တိုင်းကိုထိုးထွင်းသိမြင်နိုင်သောဗီဒီယိုများဖြင့်ဖော်ပြပြီးကျောင်းသားများကိုသဘောတရားများကိုကျွမ်းကျင်အောင်ကူညီရန်လေ့ကျင့်ခန်းများစွာပါ ၀ င်သည်။",
    },
    {
        "ka_lang": "nb",
        "le_lang": "nb",
        "name": "Norwegian Bokmål",
        "native_name": "Norsk bokmål",
        "title": "Khan Academy (Norsk bokmål)",
        "description": "Khan Academy content for Norwegian Bokmål.",
    },
    {
        "ka_lang": "nl",
        "le_lang": "nl",
        "name": "Dutch",
        "native_name": "Nederlands, Vlaams",
        "title": "Khan Academy (Nederlands)",
        "description": "Khan Academy content for Dutch.",
    },
    {
        "ka_lang": "or",
        "le_lang": "or",
        "name": "Oriya",
        "native_name": "ଓଡ଼ିଆ",
        "title": "Khan Academy (ଓଡ଼ିଆ)",
        "description": "Khan Academy content for Oriya.",
    },
    {
        "ka_lang": "pa",
        "le_lang": "pa",
        "name": "Panjabi; Punjabi",
        "native_name": "ਪੰਜਾਬੀ, پنجابی‎",
        "title": "Khan Academy (ਪੰਜਾਬੀ)",
        "description": "Khan Academy content for Panjabi; Punjabi.",
    },
    {
        "ka_lang": "pl",
        "le_lang": "pl",
        "name": "Polish",
        "native_name": "Polski",
        "title": "Khan Academy (Polski)",
        "description": "Khan Academy content for Polish.",
    },
    {
        "ka_lang": "pt",
        "le_lang": "pt-BR",
        "name": "Portuguese, Brazil",
        "native_name": "Português (Brasil)",
        "title": "Khan Academy (Português - Brasil)",
        "description": "Khan Academy oferece cursos em matemática, física, química, biologia e história. Cada matéria contém vídeos explicativos e exercícios para para a prática e revisão. Próprio para alunos do ensino médio e secundário, bem como para adultos.",
    },
    {
        "ka_lang": "pt-pt",
        "le_lang": "pt-PT",
        "name": "Portuguese, Portugal",
        "native_name": "Português (Portugal)",
        "title": "Khan Academy (Português (Portugal))",
        "description": "Khan Academy oferece cursos em matemática, física, química e biologia. Cada matéria contém vídeos explicativos e exercícios para para a prática e revisão. Próprio para alunos do ensino médio e secundário, bem como para adultos.",
    },
    {
        "ka_lang": "ro",
        "le_lang": "ro",
        "name": "Romanian; Moldavian; Moldovan",
        "native_name": "română",
        "title": "Khan Academy (română)",
        "description": "Khan Academy content for Romanian; Moldavian; Moldovan.",
    },
    {
        "ka_lang": "ru",
        "le_lang": "ru",
        "name": "Russian",
        "native_name": "русский язык",
        "title": "Khan Academy (русский язык)",
        "description": "Khan Academy content for Russian.",
    },
    {
        "ka_lang": "rw",
        "le_lang": "rw",
        "name": "Kinyarwanda",
        "native_name": "Ikinyarwanda",
        "title": "Khan Academy (Ikinyarwanda)",
        "description": "Khan Academy content for Kinyarwanda.",
    },
    {
        "ka_lang": "sk",
        "le_lang": "sk",
        "name": "Slovak",
        "native_name": "slovenčina",
        "title": "Khan Academy (slovenčina)",
        "description": "Khan Academy content for Slovak.",
    },
    {
        "ka_lang": "sr",
        "le_lang": "sr",
        "name": "Serbian",
        "native_name": "српски језик",
        "title": "Khan Academy (српски језик)",
        "description": "Khan Academy content for Serbian.",
    },
    {
        "ka_lang": "sv",
        "le_lang": "sv",
        "name": "Swedish",
        "native_name": "svenska",
        "title": "Khan Academy (svenska)",
        "description": "Khan Academy content for Swedish.",
    },
    {
        "ka_lang": "ta",
        "le_lang": "ta",
        "name": "Tamil",
        "native_name": "தமிழ்",
        "title": "Khan Academy (தமிழ்)",
        "description": "Khan Academy content for Tamil.",
    },
    {
        "ka_lang": "te",
        "le_lang": "te",
        "name": "Telugu",
        "native_name": "తెలుగు",
        "title": "Khan Academy (తెలుగు)",
        "description": "Khan Academy content for Telugu.",
    },
    {
        "ka_lang": "tr",
        "le_lang": "tr",
        "name": "Turkish",
        "native_name": "Türkçe",
        "title": "Khan Academy (Türkçe)",
        "description": "Khan Academy content for Turkish.",
    },
    {
        "ka_lang": "uk",
        "le_lang": "uk",
        "name": "Ukrainian",
        "native_name": "українська",
        "title": "Khan Academy (українська)",
        "description": "Khan Academy пропонує практичні вправи a пояснювальні відео. У нас є матеріали з математики, природничих наук, програмування, історії, історії мистецтв, економіки та багатьох інших предметів.",
    },
    {
        "ka_lang": "ur",
        "le_lang": "ur",
        "name": "Urdu",
        "native_name": "اردو",
        "title": "Khan Academy (اردو)",
        "description": "Khan Academy content for Urdu.",
    },
    {
        "ka_lang": "uz",
        "le_lang": "uz",
        "name": "Uzbek",
        "native_name": "zbek, Ўзбек, أۇزبېك‎",
        "title": "Khan Academy (zbek)",
        "description": "Khan Academy content for Uzbek.",
    },
    {
        "ka_lang": "vi",
        "le_lang": "vi",
        "name": "Vietnamese",
        "native_name": "Tiếng Việt",
        "title": "Khan Academy (Tiếng Việt)",
        "description": "Khan Academy content for Vietnamese.",
    },
    {
        "ka_lang": "zh-hans",
        "le_lang": "zh-CN",
        "name": "Chinese (China)",
        "native_name": "中文（中国）",
        "title": "Khan Academy (中文（中国）)",
        "description": "可汗学院提供与美国课程一致的视频和习题，涵盖数学、物理、化学、生物和历史。每一个主题都包括了直观的视频解释和大量的练习题目以帮助学生掌握这些学科。这些内容适合初中生、高中生和成年人学习。",
    },
]
# END AUTO-GENERATED LANGUAGE_CURRICULUM_MAP


# Auto-generated from LANGUAGE_CURRICULUM_MAP for backward compatibility
SUPPORTED_LANGS = [o["le_lang"] for o in LANGUAGE_CURRICULUM_MAP]


# Auto-generated from LANGUAGE_CURRICULUM_MAP for backward compatibility
CHANNEL_TITLE_LOOKUP = {}
for lang_entry in LANGUAGE_CURRICULUM_MAP:
    le_lang = lang_entry["le_lang"]
    if "curricula" in lang_entry:
        for curriculum in lang_entry["curricula"]:
            if curriculum.get("title"):
                CHANNEL_TITLE_LOOKUP[(le_lang, curriculum["curriculum_key"])] = curriculum["title"]
    else:
        if lang_entry.get("title"):
            CHANNEL_TITLE_LOOKUP[le_lang] = lang_entry["title"]


# Auto-generated from LANGUAGE_CURRICULUM_MAP for backward compatibility
CHANNEL_DESCRIPTION_LOOKUP = {}
for lang_entry in LANGUAGE_CURRICULUM_MAP:
    le_lang = lang_entry["le_lang"]
    if "curricula" in lang_entry:
        for curriculum in lang_entry["curricula"]:
            if curriculum.get("description"):
                CHANNEL_DESCRIPTION_LOOKUP[(le_lang, curriculum["curriculum_key"])] = curriculum["description"]
    else:
        if lang_entry.get("description"):
            CHANNEL_DESCRIPTION_LOOKUP[le_lang] = lang_entry["description"]


# Auto-generated from LANGUAGE_CURRICULUM_MAP for backward compatibility
# map from le-utils codes to language codes used in the Khan Academy TSV exports
KHAN_ACADEMY_LANGUAGE_MAPPING = {}
for lang_entry in LANGUAGE_CURRICULUM_MAP:
    le_lang = lang_entry["le_lang"]
    ka_lang = lang_entry["ka_lang"]
    if le_lang != ka_lang:
        KHAN_ACADEMY_LANGUAGE_MAPPING[le_lang] = ka_lang


def get_channel_title(lang=None, variant=None):
    """
    Return KA channel title for le-utils code `lang` and variant `variant`.
    """
    if variant and (lang, variant) in CHANNEL_TITLE_LOOKUP:
        return CHANNEL_TITLE_LOOKUP[(lang, variant)]
    elif lang in CHANNEL_TITLE_LOOKUP:
        return CHANNEL_TITLE_LOOKUP[lang]
    else:
        lang_obj = getlang(lang)
        title = "Khan Academy ({})".format(lang_obj.first_native_name)
        return title


def get_channel_description(lang=None, variant=None):
    """
    Find KA channel description for le-utils code `lang` and variant `variant`.
    """
    if variant and (lang, variant) in CHANNEL_DESCRIPTION_LOOKUP:
        return CHANNEL_DESCRIPTION_LOOKUP[(lang, variant)]
    elif lang in CHANNEL_DESCRIPTION_LOOKUP:
        return CHANNEL_DESCRIPTION_LOOKUP[lang]
    else:
        lang_obj = getlang(lang)
        description = "Khan Academy content for {}.".format(lang_obj.name)
        return description