#!/usr/bin/env python
# Copyright (C) 2015 Shea G Craig <shea.craig@da.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
 ______            _        _
(  ___ \ |\     /|( \      | \    /\
| (   ) )| )   ( || (      |  \  / /
| (__/ / | |   | || |      |  (_/ /
|  __ (  | |   | || |      |   _ (
| (  \ \ | |   | || |      |  ( \ \
| )___) )| (___) || (____/\|  /  \ \
|/ \___/ (_______)(_______/|_/    \/
 _______  ______   _______
(  ____ )(  __  \ (  ____ \
| (    )|| (  \  )| (    \/
| (____)|| |   ) || (__
|  _____)| |   | ||  __)
| (      | |   ) || (
| )      | (__/  )| )
|/       (______/ |/
[ ______   _______           _        _        _______  _______  ______
(  __  \ (  ___  )|\     /|( (    /|( \      (  ___  )(  ___  )(  __  \
| (  \  )| (   ) || )   ( ||  \  ( || (      | (   ) || (   ) || (  \  )
| |   ) || |   | || | _ | ||   \ | || |      | |   | || (___) || |   ) |
| |   | || |   | || |( )| || (\ \) || |      | |   | ||  ___  || |   | |
| |   ) || |   | || || || || | \   || |      | |   | || (   ) || |   ) |
| (__/  )| (___) || () () || )  \  || (____/\| (___) || )   ( || (__/  )
(______/ (_______)(_______)|/    )_)(_______/(_______)|/     \|(______/

Find all of the links to pdf's on a webpage and download them all.

Streams the downloads so memory doesn't get bogged down. If it fails
or has to be restarted, will check for already-downloaded files or
incomplete files and do the right thing.

Written originally to hog down a bunch of old rpg materials for a
nostalgia-gasm.

Lots of room for improvement ;)
"""

import argparse
import os
import re
import sys
import urllib

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scrape_url")
    parser.add_argument("-o", "--output_dir", help="Directory to save output "
                        "in.")
    args = parser.parse_args()
    page_to_scrape = args.scrape_url

    response = requests.get(page_to_scrape)

    files = []
    pdf_search = re.compile(r'<a href=[\'"]'
                            r'([/\w% -]*\.pdf)[\'"]')

    for line in response.iter_lines():
        matches = re.finditer(pdf_search, line)
        for match in matches:
            download_url = match.group(1)
            if not download_url.startswith("http"):
                # Relative URL-cat onto page URL.
                download_url = os.path.join(os.path.dirname(page_to_scrape),
                                            download_url)
            files.append(download_url)
            print "Adding '{} to download list.".format(download_url)

    if page_to_scrape.upper().endswith((".PHP", ".HTML", ".HTML")):
        base_url = page_to_scrape.rsplit("/", 1)[0]
    else:
        base_url = page_to_scrape

    output_dir = os.path.expanduser(args.output_dir) or ""
    failures = []
    try:
        for download_url in files:
            output_file = urllib.unquote(
                os.path.basename(download_url).replace("/", "-"))
            output_path = os.path.join(output_dir, output_file)
            try:
                size = int(
                    requests.head(download_url).headers["content-length"])
            except KeyError:
                # Something went wrong, add to the failures list and move on.
                print "Failed to download %s" % download_url
                failures.append(download_url)
                continue

            if (os.path.exists(output_path) and
                    size != os.stat(output_path).st_size):
                print ("File '%s' incomplete, downloading again from scratch."
                       % output_path)
            elif not os.path.exists(output_path):
                print "Downloading '%s'" % download_url
            else:
                print "Already downloaded '{}'.".format(download_url)
                continue

            print "Downloading {:,} bytes".format(size)

            with open(output_path, 'wb') as f:
                response = requests.get(download_url, stream=True)
                for segment in response.iter_content():
                    f.write(segment)
    except KeyboardInterrupt:
        print "User quit!"
    except Exception as e:
        print e, type(e)

    finally:
        if failures:
            print "Failed to download the following:"
            for failure in failures:
                print failure


if __name__ == "__main__":
    main()
