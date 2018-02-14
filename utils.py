from le_utils.constants.languages import getlang, _LANGLOOKUP


def get_lang_code_list(lang):
    """
    Returns a list of language codes that has a similar language name to the specified language code.

    Example 1: Swahili language has {
                "sw":{ "name":"Swahili", "native_name":"Kiswahili" },
                "swa":{ "name":"Swahili", "native_name":"Kiswahili" },
            }
            Function call is `get_lang_code_list("sw")`.
            Return is `["sw", "swa"]`.

    Example 2: Somali language has {
                "som":{ "name":"Somali", "native_name":"Soomaaliga" },
                "so":{ "name":"Somali", "native_name":"Soomaaliga, af Soomaali" },
            }
            Function call is `get_lang_code_list("so")`.
            Return is `["so", "som"]`.
    """
    lang_name = getlang(lang).name

    # TODO: Replace with list comprehension?
    # lang_code_list = [obj[0] for obj in langlookup.items() if obj[1]["name"] == lang_name]

    lang_code_list = []
    for obj in _LANGLOOKUP.items():
        name = obj[1].name.split(',')[0]
        if name == lang_name:
            lang_code_list.append(obj[0])
    # MUST: Return a sorted list to make debugging easier.
    return sorted(lang_code_list)
