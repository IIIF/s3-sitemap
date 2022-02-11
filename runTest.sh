#!/bin/bash

target="http://localhost:3000/"
filename=""
if [ $# -eq 1 ]
then
    filename=$1
else
    filename=github-webhook-example.json
fi

curl -X POST -H "Content-Type: application/json" -d @$filename $target

echo ""
