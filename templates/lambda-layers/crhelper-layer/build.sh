#!/bin/sh
# Build the layer file
pip install -r requirements.txt -t python/lib/python3.7/site-packages
zip -r crhelper-layer.zip python