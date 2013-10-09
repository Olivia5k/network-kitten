"""
Helper module to generate human readable semi-unique ids.

Combines an adjective and an animal from semi-exhaustive lists of both kinds to
create a random but human friendly id.

Currently, the returned strings can be between 6 (bad_ox) and 45
(disillussioned_eastern-diamondback-rattlesnake) characters long and there are
about 500k different choices.


TODO: Split from the kitten project and upload as a standalone project to pypi
and github.

"""

from os.path import join, dirname
import random
import json

DIR = join(dirname(__file__), 'static')

ADJECTIVES = json.load(open(join(DIR, 'adjectives.json')))
ANIMALS = json.load(open(join(DIR, 'animals.json')))


def random_name(max_length=45):
    name = None
    while name is None or len(name) > max_length:
        name = "%s_%s" % (random.choice(ADJECTIVES), random.choice(ANIMALS))

    return name
