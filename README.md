# har2lilua

Converts Browser archive files (HAR) to LoadImpact (loadimpact.com)
user scenario scripts (Lua).

HAR files can be created using the dev tools of modern browsers; they
form a record of the network actions performed during browser
sessions.  This program converts such a HAr file to a user scenario
script that can be loaded into the LoadImpact service for performance
testing.

har2lilua is currently lacking some features, like form handling.

## Installation

`har2lilua` is not currently on PyPi.  It requires the `dateutils`
package. To install:

1. Clone repo 
2. `pip install dateutils`  (e.g. in a virtualenv)
3. The program in question is `har2lilua/har2lilua.py`.

## Usage

1. Get a HAR file. You can get one by using e.g. Firefox's or Chrome's 
   dev consoles; choose the Network tab/section. Reload the page and
   click a link. Then right-click in the console and select to save 
   as HAR. Save as, say, `mytest.har`.
2. Run `python har2lilua path/to/mytest.har`. This creates `mytest.lua`. 
3. Go to loadimpact.com, log in to the dashboard and copy/paste the contents 
   of `mytest.lua` as a new user scenario. You can then tweak it
   manually if you want.

