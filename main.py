
"""
Super quick and hacky way of getting all the NPMjs packages that use eslint-scope

12/07/2018 hack of eslint-scope: https://github.com/eslint/eslint-scope/issues/39
"""

# Native
import sys
import time
import json
from collections import OrderedDict

# 3rd-Party
import requests

# Proprietary




# Add some headers so admins of the services we are using might be kind :)
HEADERS = {
    'User-Agent': 'https://github.com/m3talstorm/eslint-finder - https://github.com/eslint/eslint-scope/issues/39',
}

# Package name we are looking for
NAME = "eslint-scope"
# The file to save results to
FILE = './packages.json'



packages = {}

payload = OrderedDict([
    ('group_level', 2),
    ('startkey', json.dumps([NAME])),
    ('endkey', json.dumps([NAME, {}])),
    ('limit', 10000),
    ('skip', 0),
    ('state', 'update_after')
])

print("Getting packages from npmjs...")

skimdb = requests.get('https://skimdb.npmjs.com/registry/_design/app/_view/dependedUpon', params=payload, headers=HEADERS)

if not skimdb:
    print("Cannot get list of packages from skimdb" % (skimdb.status_code))
    sys.exit(0)

data = skimdb.json()

rows = data['rows']

if rows:
    print("Got packages from npmjs")
else:
    raise Exception("Got no packages back from npmjs")

for row in rows:
    #
    package = row['key'][1]
    #
    packages[package] = ()



print("Finding repositories for each package ...")

FIND = '"repository":'

for package, eslint in packages.items():

    if eslint:
        print("Skipping package '%s'" % (package))
        continue

    print("Finding repo for '%s'..." % (package))

    #
    npmjs = requests.get("https://www.npmjs.com/package/%s" % (package), headers=HEADERS)

    if not npmjs:

        if npmjs.status_code == 429:
            # We are being rate limited
            print("npmjs is rate-limiting us, waiting...")
            time.sleep(10)
        else:
            print("npmjs package doesn't exist (%s)" % (npmjs.status_code))

        continue

    content = str(npmjs.content)

    #
    start = content.find(FIND)
    end = content.find('"', start + len(FIND) + 1)
    #
    url = content[start + len(FIND) + 1:end]

    if 'https://github.com/' in url:
        print("Github repo found for '%s' (%s)" % (package, url))
    else:
        print("Github repo not found for npmjs package '%s'" % (package))
        continue
    #
    url = url.replace('https://github.com/', '')

    #
    github = requests.get("https://raw.githubusercontent.com/%s/master/package.json" % (url), headers=HEADERS)

    if not github:

        if github.status_code == 429:
            # We are being rate limited
            print("Github is rate-limiting us, waiting...")
            time.sleep(10)
        else:
            print("Github repo doesn't exist or doesn't have a package.json (%s)" % (github.status_code))

        continue

    data = github.json()
    #
    peer = data.get('peerDependencies', {}).get(NAME, '')
    deps = data.get('dependencies', {}).get(NAME, '')
    dev = data.get('devDependencies', {}).get(NAME, '')
    #
    packages[package] = (peer, deps, dev)

    if peer or deps or dev:
        print("Package %s has a dependency on %s versions %s" % (package, NAME, packages[package]))
    else:
        print("Package %s has no dependency on %s" % (package, NAME))

    # Save the JSON file for each package so if we terminate, we still save the previous results
    with open(FILE, 'w') as fd:
        json.dump(packages, fd)

    # Be nice - don't hammer them :)
    time.sleep(1)
