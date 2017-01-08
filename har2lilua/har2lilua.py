#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
HAR2LILua

- Converts HAR (http archive) format files (e.g. extracted from a modern
text browser) into a LoadImpact (loadimpact.com) user scenario script in
Lua.

"""

from __future__ import unicode_literals
from __future__ import print_function
import re
import json
from string import Template
from io import open
from dateutil.parser import parse as dateutilparse
from collections import defaultdict

__version__ = 0.5

# handle py2/3 string comparisons
try:
    basestring
except NameError:
    basestring = str


# output string templates

_LUA_BATCH_ARG = Template("""    { $method,
       $url,
       $ip,
       $headers,
       $data,
       $auto_redirect, $auto_decompress, $response_body_bytes, $base64_encoded_body, $report_results }""")

_LUA_REQUEST = Template("""http.request( $method,
    $url,
    $ip,
    $headers,
    $data,
    $auto_redirect, $auto_decompress, $response_body_bytes, $base64_encoded_body, $report_results )""")

_LUA_SINGLE = Template("""
-- $comment

$body
""")
_LUA_PAGE = Template("""
-- Page $comment

http.page_start("$pageref")

responses = http.request_batch({
$body
})

http.page_end("$pageref")
""")

_LUA_ALL = Template("""-- LoadImpact user scenario script $outfile
-- converted by har2lilua $version from $infile (created by $creator).
$body

-- Sleep client
client.sleep(math.random(20, 40))
""")

_LUA_UA_FALLBACK = \
    Template("User-agent string based on browser name $name $version.$comment")

# these are fallbacks in case the user-agent must be determined from
# the browser name only; one may need to experiment with more browsers
# to see just how generically useful they are.
_BROWSER_UA_FALLBACKS = {
    "firefox": "Mozilla/5.0 Gecko Firefox",
    "iceweasel": "Mozilla/5.0 Gecko Firefox",
    "seamonkey": "Mozilla/5.0 Gecko Firefox",
    "chrome": "Mozilla/5.0 AppleWebKit (KHTML, like Gecko) Chrome Safari",
    "chromium": "Mozilla/5.0 AppleWebKit (KHTML, like Gecko) Chrome Safari",
    "safari": "Mozilla/5.0 AppleWebKit (KHTML, like Gecko) Chrome Safari",
    "konqueror": "Mozilla/5.0 AppleWebKit (KHTML, like Gecko) Chrome Safari",
    "opera": "Opera/9.80 Presto",
    "ie": "Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko"
        }

# helper function

_RE_LUA_BRACKETS = re.compile(r"\[(=*)\[|\](=*)\]")
def _clean_lua(string, brackets=False):
    """
    Clean python string to valid lua

    Args:
        string (str): String to clean
        brackets (bool, optional): Determines ifstring should be treated as
            an [[ ]] enclosed lua string. Using [[ ]] over escaping " and '
            makes for a more readable output result for things like
            POST data.
    Notes:
        Lua strings defined by [[ ]] both handle line breaks and
        embedded "/', but if there are embedded [[ ]] or [=..=[ ]=..=]
        we must use correct brackets to escape those ([====[ ...
        ]====] with the number of '=' different from any embedded in
        the string).

    """
    if brackets and not string.endswith("]"):
        try:
            nbrackets = max(match.group().count("=") for match
                    in _RE_LUA_BRACKETS.finditer(string) if match)
            nbrackets = nbrackets + 1
        except ValueError:
            nbrackets = 0
        return "[%s[%s]%s]" % ("=" * nbrackets, string, "=" * nbrackets)
    else:
        return "\"%s\"" % string.replace("\"", "\\\"").replace("\'", "\\\'")


# HAR -> loadimpact converters. These all takes a HAR dict structure
# and returns a Lua code snippet.

def _validate_version(hardict):
    """
    Validate HAR version

    Args:
        hardict (dict): HAR dictionary
    Raises:
        RuntimeError if HAR version is not supported

    """
    version = hardict["log"]["version"]
    if not 1 <= float(version) < 2:
        raise RuntimeError("HAR version %s is not supported." % version)


def _get_creator(hardict):
    """
    Get creator of HAR file.
    """
    creator = hardict["log"]["creator"]
    return "%s %s%s" % (creator["name"], creator["version"],
       " (Comment: %s)" % creator["comment"] if creator.get("comment") else "")

def _get_user_agent(hardict):
    """
    Get the user agent key and parse it to a user-agent string.

    Args:
        hardict (dict): HAR dictionary
    Returns:
        luastr (str): Lua code snippet using
            http.set_user_agent_string()

    """
    # Only the request headers store the actual user agent string, so
    # we first try to get it that way. This is not actually defined in
    # the HAR spec though.
    user_agent_string = None
    comment = "User-agent string based on request headers."
    for entry in hardict["log"]["entries"]:
        headers = entry["request"]["headers"]
        for header in headers:
            if header.get("name").lower() in ("user-agent", "useragent", "ua"):
                user_agent_string = header["value"]
                break
    if not user_agent_string:
        # we couldn't get the ua from the request headers, so we fall
        # back to using the 'browser' key from HAR, if it exists.
        browser_dict = hardict["log"].get("browser")
        if browser_dict:
            name = browser_dict["name"]
            version = browser_dict["version"]
            comment = browser_dict.get("comment", "")
            comment = " (Comment: %s)" % comment if comment else ""
            comment = _LUA_UA_FALLBACK.safe_substitute(name=name,
                                                       version=version,
                                                       comment=comment)
            # try to convert
            user_agent_string = _BROWSER_UA_FALLBACKS.get(name.lower())

    if user_agent_string:
        body = 'http.set_user_agent_string("%s")' % user_agent_string
    else:
        comment = "Could not resolve User-agent string; "\
                  "relying on LoadImpact default."
        body = ""
    return _LUA_SINGLE.safe_substitute(comment=comment, body=body)


def _get_entry(entrydict, batch=False):
    """
    Parse HAR entry structure.

    Args:
        eventdict (dict): One entry dict from the "entries" array of
            the HAR.
        batch (bool, optional): If this return should be part of a
            batch request or not.
    Returns:
        lua (str): If `batch=False` then this is http.request of the
            right type. Otherwise it is one argument of a batch_request.

    """
    # method, url, ip, headers, data, auto_redirect=True, auto_decompress=False
    # response_body_bytes=0, base64_encoded_body=False, report_results=True,
    # connect_timeout=120, timeout=120
    request = entrydict["request"]
    response = entrydict["response"]

    method = request["method"]
    url = request["url"]
    ipaddr = entrydict.get("serverIPAddress")
    resp_body_bytes = response["bodySize"] if response["bodySize"] > 0 else 0
    request_headers = dict((req["name"], req["value"])
                            for req in request["headers"])

    # processing of data with postData (POST/PUT/PATCH)
    postdata = request.get("postData", {})
    data = None
    postdata_mimetype = postdata.get("mimeType", "")
    # there is no encoding info in the HAR request block except for
    # what might be # spied within the mimetype; and while `params` or
    # multipart/form-data (in `text`) contains embedded Content-type
    # info, this would suggest a mixed plain-text and base64 data which
    # does not make sense for LI's http.request's `base64_encoded_body`
    # keyword (which seems  to want to be set only if the entirety of
    # the body is base64-encoded).

    base64_encoded_body = "true" if "base64" in postdata_mimetype else "false"
    # params and text are exclusive to one another in HAR spec but
    # this is NOT respected by e.g. Chrome, duplicating the data.
    params = postdata.get("params")
    text = postdata.get("text")
    if text:
        # HAR spec suggests 'text' only holds data of content-type
        # multipart/form-data and text/plain, but Chrome outputs also
        # application/x-www-form-urlencoded data in raw form.
        # Note: This is also where form data could be parsed for a future
        # implementation.
        data = text
    elif params:
        # 'params' represents URL-encoded data parameters for mimetype
        # application/x-www-form-urlencoded; if we don't have it
        # duplicated in the 'text' field we need to recreate the
        # urlencoded string manually.
        data = "&".join("%s=%s" %
                (param["name"], param["value"]) for param in params)

    request_headers_lua = ", ".join("[\"%s\"]=%s" %
            (key, _clean_lua(value)) for key, value in request_headers.items())
    request_headers_lua = "{%s}" % (request_headers_lua
                                    if request_headers_lua else "nil")

    formatdict = {"method": '"%s"' % method,
                  "url": '"%s"' % url,
                  "ip": '"%s"' % ipaddr if ipaddr else "nil",
                  "headers": request_headers_lua,
                  "data": _clean_lua(data, brackets=True) if data else "nil",
                  "auto_redirect": "nil",   #Use default
                  "auto_decompress": "nil", #Use default
                  "response_body_bytes": resp_body_bytes,
                  "base64_encoded_body": base64_encoded_body,
                  "report_results": "nil"}
    if batch:
        return _LUA_BATCH_ARG.safe_substitute(**formatdict)
    else:
        return _LUA_REQUEST.safe_substitute(**formatdict)


def _parse_entries(hardict):
    """
    Parse all entries, grouping those that have a page reference into
    page blocks. This will also handle requests occurring outside the
    scope of a page, retaining the original call timing.

    Args:
        hardict (dict): HAR dictionary
    Returns:
        luastr (str): Lua code snippet with page

    """
    # make sure pages and events are sorted in start-order since this
    # is not guaranteed by the HAR standard. This also hadles events
    # that occur outside of the context of a page.
    pages = hardict["log"].get("pages", [])
    data = sorted(pages + hardict["log"]["entries"],
            key=lambda dat: dateutilparse(dat["startedDateTime"]))

    # we want to save the time-deltas until the *next* entry in the list
    if len(data) > 1:
        dtimes = [dateutilparse(dat["startedDateTime"]) for dat in data]
        dtimes = [dtimes[i + 1] - dtimes[i] for i in range(len(dtimes)-1)]
    else:
        dtimes = [0]

    # we make a page->event mapping for quick lookup
    entries = defaultdict(list)
    for entry in sorted(hardict["log"]["entries"],
                key=lambda ev: dateutilparse(ev["startedDateTime"])):
        entries[entry.get("pageref", None)].append(entry)

    lua = []
    for idat, dat in enumerate(data):
        comment = dat.get("comment", "")
        if "id" in dat:
            # a page.
            title = dat["title"]
            pageref = dat["id"]
            comment = "%s (HAR pageref '%s')%s" % (title, pageref,
                            " (Comment: %s)" % comment if comment else "")
            body = []
            entry_time = 0
            for entrydict in entries[pageref]:
                body.append(_get_entry(entrydict, batch=True))
                entry_time += entrydict["time"] if entrydict["time"] > 0 else 0
            if body:
                lua.append(_LUA_PAGE.safe_substitute(comment=comment,
                                                     pageref=pageref,
                                                     body=",\n\n".join(body)))
            dtime = dtimes[idat]
            if dtime.microseconds > 0:
                # we should sleep before triggering the next page in
                # order to best emulate the user case we recorded. But
                # since the batch-requests block we must remove the
                # time that has already passed from page load.
                onload = dat["pageTimings"].get("onLoad", -1)
                onload = onload if onload and onload >= 0 else 0
                comment = dat["pageTimings"].get("comment", "")
                # Note - setting 10 ms as minimum sleep and assuming
                # entry time and onload time are independent of each
                # other.
                sleeptime = max(10, dtime.microseconds - entry_time - onload)
                lua.append(["-- pause until next page%s." %
                            ((" (Comment: %s)" % comment) if comment else ""),
                            "client.sleep(%s, 1000)" % sleeptime])

        elif "pageref" not in dat:
            # an entry outside the scope of a page
            comment = "Request outside page%s" % (
                        " (Comment: %s" % comment if comment else "")
            lua.append(_LUA_SINGLE.safe_substitute(comment=comment,
                                                   body=_get_entry(dat)))

    return "\n".join(lua)

# access functions

def convert(harstring, infilename="test.har", outfilename="test.lua"):
    """
    Convert HAR string to LoadImpact Lua string.

    Args:
        harstring (str): Valid string with HAR data, possible to
            parse as JSON..
        infilename (str, optional): input HAR filename, for pretty-
            printing in the converted string.
        outfilename (str, optional): output HAR filename, for pretty-
            printing in the converted string.
    Returns:
        luestring (str): The converted LoadImpact user case string,
            in Lua.

    """
    hardict = json.loads(harstring)

    _validate_version(hardict)
    creator = _get_creator(hardict)
    luastring = _get_user_agent(hardict)
    luastring += _parse_entries(hardict)

    return _LUA_ALL.safe_substitute(infile=infilename,
                                outfile=outfilename,
                                body=luastring,
                                creator=creator,
                                version=__version__)


def har2lilua(infile="test.har", outfile="test.lua"):
    """
    Load HAR file and convert it to a LoadImpact Lua file.

    Args:
        infile (str, optional): File name of HAR file to parse.
        outfile (str, optional): File name of output Lua file.

    """
    with open(infile, "r", encoding='utf-8') as fil:
        harstring = fil.read()

    luastring = convert(harstring, infilename=infile, outfilename=outfile)

    with open(outfile, "w") as fil:
        fil.write(luastring)

# command line handler

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("infile", help="HAR file to convert.")
    parser.add_argument("outfile", nargs="?", default=None,
             help="LoadImpact user scenario script to create. "
                  "Defaults to <infile>.lua.")

    args = parser.parse_args()
    infile = args.infile
    outfile = args.outfile
    outfile = outfile if outfile else "%s.lua" % (infile.rsplit(".", 1)[0])

    luastring = har2lilua(infile, outfile)

    print("Converted '%s' -> '%s'." % (infile, outfile))
