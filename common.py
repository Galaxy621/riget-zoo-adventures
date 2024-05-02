from flask import redirect, url_for

def redirect_home():
    return redirect(url_for("pages.index"))

def char_in_string(testString, chars) -> bool:
    for char in chars:
        if char in testString:
            return True
        
def get_boolean_js(val):
    if val == "true": return True
    if val == "false": return False
    return False