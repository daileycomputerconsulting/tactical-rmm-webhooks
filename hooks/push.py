#!/usr/bin/env python
import logging
import sys

logging.basicConfig(stream=sys.stderr)
logging.debug("Loading push")

from tactical_rmm.tactical_api import compare_scripts

if __name__ == "__main__":
    logging.warning("Main push")
    compare_scripts()