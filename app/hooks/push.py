#!/usr/bin/env python
import logging
import sys
import os
logging.basicConfig(stream=sys.stderr)
logging.debug("Loading push")

#from  tactical_api import compare_scripts
#from tactical_api import compare_scripts # .tactical_api import compare_scripts
#from app.webhooks import application
import hooks.tactical_rmm.tactical_api as tactical_api

def run(payload):
    print(os.getcwd())
    #application.logger.info('test')
    logging.warning("Got Push")
    tactical_api.compare_scripts()
    return {"msg": "compared scripts"}

if __name__ == "__main__":
    
    print(os.getcwd())
    #application.logger.info('test main')
    
    logging.warning("Main push")
    #compare_scripts()