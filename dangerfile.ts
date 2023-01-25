import { spawnSync } from "child_process";
import { createHash } from "crypto";
import { danger, fail, message, schedule, warn } from "danger";
import * as fs from 'fs';

// const docs = danger.git.fileMatch("**/*.md")
// const app = danger.git.fileMatch("src/**/*.ts")
// const tests = danger.git.fileMatch("*/__tests__/*")
const changelogs = danger.git.fileMatch("changelogs/unreleased/*")
const requirmentsChanged = danger.git.modified_files.includes("requirements.txt")

function checkSum(name:string) {
    return createHash("sha256").update(fs.readFileSync(name, 'utf-8')).digest("hex")
}

let prevSha = checkSum("locales/mkbot.pot")

spawnSync("python", ["tools/pygettext.py", "-p locales", "-d mkbot", "-v", "-D", "--no-location", "src/bot", "src/lib"])

let CurSha = checkSum("locales/mkbot.pot")

if (prevSha != CurSha) {
    fail("Changes in translated strings found, please update file `locales/mkbot.pot` by running: `scripts/gettext.bat`")
}

schedule(async () => {
    let pr = await danger.github.api.issues.get({ owner: danger.github.thisPR.owner, repo: danger.github.thisPR.repo, issue_number: danger.github.thisPR.number })

    if (!pr.data.milestone) {
        warn("This merge request does not refer to an existing milestone.")
    }
})

if (!changelogs.created && !danger.github.issue.labels.find(e => e.name === "Changelog Entry: Skipped")) {
    fail("Please add a [changelog entry](https://github.com/mgylabs/mkbot/tree/main/changelogs) for your changes.")
}

if (requirmentsChanged) {
    schedule(async () => {
        await danger.github.api.issues.addLabels({owner: danger.github.thisPR.owner, repo: danger.github.thisPR.repo, issue_number: danger.github.thisPR.number, labels: ["dependencies", "python"]})
    })
    message("This pull request adds, or changes a Python dependency. Please [validate hook files](https://github.com/mgylabs/mkbot/wiki/How-to-Contribute#validate-hook-files).")
}
