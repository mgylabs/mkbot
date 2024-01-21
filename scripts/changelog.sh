#!/bin/bash

cd "$(dirname "$0")/.."

ch_title=""
ch_type=""
ch_pr=""

read -p "Title> " ch_title

if [ -z "$ch_title" ]
then
    echo "Title is required."
    exit 1
fi

echo

read -p "Pull Request Number> " ch_pr

echo

select num in "Feature" "Change" "Bug Fix" "Other"
do
    case $num in
        "Feature")
            ch_type="features"
            break
            ;;
        "Change")
            ch_type="changes"
            break
            ;;
        "Bug Fix")
            ch_type="bug fixes"
            break
            ;;
        "Other")
            ch_type="others"
            break
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
done

low_ch_title=$(echo "$ch_title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

if [ -z "$ch_pr" ]
then
    ch_filename="changelogs/unreleased/$low_ch_title.yml"
else
    ch_filename="changelogs/unreleased/$ch_pr-$low_ch_title.yml"
    ch_pr=" $ch_pr"
fi

ch_title=" $ch_title"

cat << EOF > "$ch_filename"
---
title:$ch_title
pull_request:$ch_pr
type: $ch_type
EOF

echo
echo "A changelog was created at $ch_filename"
