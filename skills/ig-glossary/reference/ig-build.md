# Optional stage: build the dry-run copy and compare QA

Proves that applying every suggested edit still builds, and that the publisher's QA counts do not get worse. Needs the HL7 IG Publisher toolchain (Java, Node + SUSHI, Jekyll/Ruby) already working for this IG, plus `jq`. Budget 20–40 minutes per build.

## 1. Baseline build (pristine snapshot copy)

```bash
IG=<path to the IG checkout>            # the snapshot in config.yaml
TAG=<tag>                               # ig.tag in config.yaml
RUN=<run directory>
git -C $IG worktree add --detach $IG-baseline $TAG
cp $IG/input-cache/publisher.jar $IG-baseline/input-cache/ 2>/dev/null || true   # or _updatePublisher.sh
cd $IG-baseline && bash ./_genonce.sh > build.log 2>&1
mkdir -p $RUN/data/qa && cp output/qa.json $RUN/data/qa/qa-baseline.json
echo "broken_links=$(grep -oE 'broken links = [0-9]+' output/qa.html | grep -oE '[0-9]+' | head -1)" > $RUN/data/qa/qa-baseline.txt
jq '{errs, warnings, hints}' $RUN/data/qa/qa-baseline.json
```

## 2. Dry-run build (every suggestion applied)

Step 8 of the skill already created `$IG-dryrun` and applied the rows (`drifted 0`). Then:

```bash
cd $IG-dryrun && bash ./_genonce.sh > build.log 2>&1
grep -m1 -E '[0-9]+ Errors' build.log
for k in errs warnings hints; do
  printf "%-10s baseline %-5s dryrun %-5s\n" $k "$(jq ".$k // 0" $RUN/data/qa/qa-baseline.json)" "$(jq ".$k // 0" output/qa.json)"
done
echo "broken_links baseline $(grep -oE '[0-9]+' $RUN/data/qa/qa-baseline.txt) dryrun $(grep -oE 'broken links = [0-9]+' output/qa.html | grep -oE '[0-9]+' | head -1)"
```

**Pass:** no count is higher in the dry run than the baseline. **Expected exception:** if a row changes an artifact *title*, the publisher warns that the title must be registered in HL7's artifact list; that is one warning per changed title and is part of the rename work, not a defect. Record the outcome in `config.yaml` as `summary.build_note` (one sentence, e.g. "Every suggested edit was applied to a copy of the guide, which built with no new errors and one expected warning about a changed artifact title.") and re-run `summary.py`.

## 3. Re-scan the dry run (optional)

Shows which rule hits remain after every edit, and which of those are explained (dismissed, Manual, rejected):

```bash
mkdir -p $RUN/dryrun-scan && cd $RUN/dryrun-scan
sed "s#^  snapshot: .*#  snapshot: $IG-dryrun#" $RUN/config.yaml > config.yaml
cp $RUN/rulebook.yaml .
cp $RUN/figure_transcripts.yaml . 2>/dev/null || true
python3 $SCRIPTS/extract.py && python3 $SCRIPTS/scan.py
mkdir -p $RUN/data/dryrun && cp data/hits.jsonl $RUN/data/dryrun/hits.jsonl
cd $RUN && python3 $SCRIPTS/apply.py --residuals
```
Any `UNEXPLAINED` line is a hit nobody dispositioned; look at it before sharing the workbook.

Clean up: `git -C $IG worktree remove $IG-baseline && git -C $IG worktree remove $IG-dryrun && rm -rf $RUN/dryrun-scan`.
