Tactical RMM Webhooks

Manage your TRMM scripts using git!

Will patch scripts in tactical rmm upon push to main when changes are detected

deploy with docker, gunicorn, or in debug mode with flask

pair this with another repo containing your scripts. example:

https://github.com/daileycomputerconsulting/trmm-scripts-example

set env variables:

TRMM_TOKEN

TRMM_URL

GH_TOKEN

GH_ORG

GH_REPO=tactical-rmm-scripts
