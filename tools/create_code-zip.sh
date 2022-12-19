#!/bin/bash

# run from the tools folder before commiting changes made to files in the ./code folder to update code.zip in the templates folder.

cd ../code
zip -r code.zip *
mv ./code.zip ../templates