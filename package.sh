#!/bin/sh
# Generate one file with compressed and concatenated JavaScript
uglifyjs quarterapp/resources/static/libraries/moment.min.js \
    quarterapp/resources/static/libraries/pikaday.min.js \
    quarterapp/resources/static/scripts/qa.js \
    quarterapp/resources/static/scripts/qa.validator.js \
    quarterapp/resources/static/scripts/qa.palette.js \
    quarterapp/resources/static/scripts/qa.switcher.js \
    quarterapp/resources/static/scripts/qa.category.js \
    quarterapp/resources/static/scripts/qa.activity.js \
    quarterapp/resources/static/scripts/qa.timesheet.js \
    quarterapp/resources/static/scripts/qa.report.js \
    --compress --output quarterapp/resources/static/scripts/quarterapp.min.js

# And for CSS
lessc quarterapp/resources/static/styles/qa.compile.less > quarterapp/resources/static/styles/quarterapp.css
cat quarterapp/resources/static/styles/quarterapp.css | cleancss -o quarterapp/resources/static/styles/quarterapp.min.css

# Make the python distribution
python setup.py sdist