# ghSpyglass

Small CLI utility to count GitHub repositories matching topics/keywords between two dates.

Usage examples

Run a basic aggregate count:

```bash
python3 gh_spyglass.py --start 2020-01-01 --end 2020-12-31 --topics cli api --keywords tool
```

Count per-term:

```bash
python gh_spyglass.py --start 2020-01-01 --end 2020-12-31 --topics cli api --per-term
```

Set a GitHub token to avoid low rate limits:

```bash
export GITHUB_TOKEN=ghp_...
```
# ghSpyglass
Pull github stats and make some graphs
