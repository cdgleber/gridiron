# Gridiron — NFL Pool Standings

A static leaderboard for a "pick your teams" NFL pool. Each participant
picks a set of NFL teams; a team scores `wins − divisional losses`; a
participant's score is the sum across their picks. Standings come from
ESPN's public API — no RapidAPI key, no database, no server.

## How scoring works

For each team: `score = wins - divisional_losses`.
For each better: `score = sum(team.score() for team in their picks)`.

## Setting up a new season's pool

Edit `picks.txt` at the repo root. Format: a better's name on one line,
followed by one NFL team name per line (must exactly match ESPN's team
name, e.g. `Buffalo Bills`, not `Bills`), with a blank line between
betters:

```
Alice
Buffalo Bills
Kansas City Chiefs

Bob
Dallas Cowboys
Baltimore Ravens
```

## Running it locally

```bash
uv run gridiron                       # writes index.html for the current year
uv run gridiron --season 2025         # override the season
uv run gridiron --picks other.txt     # use a different picks file
```

Requires `picks.txt` to only contain team names ESPN recognizes — an
unknown pick raises an error naming the better and the bad team name
instead of silently dropping it.

## Running the tests

```bash
uv run pytest
```

## Automatic updates

`.github/workflows/update-standings.yml` runs `uv run gridiron` on a
schedule (Tuesday mornings, after Monday Night Football) and on manual
trigger, committing `index.html` back to `main` when it changes.

## Hosting on GitHub Pages

1. Push this repo to GitHub.
2. In the repo, go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to `Deploy from a
   branch`, branch `main`, folder `/ (root)`. Save.
4. Your page is live at `https://<username>.github.io/<repo>/` within a
   few minutes.

## Using your own domain

1. Buy/own a domain (or use a subdomain of one you already have, e.g.
   `standings.example.com`).
2. Add a `CNAME` file to the repo root containing just your domain, e.g.:
   ```
   standings.example.com
   ```
   (GitHub Pages regenerates this automatically once you set the custom
   domain in the UI in step 4 below — you can also create it yourself.)
3. At your DNS provider, create a record pointing at GitHub Pages:
   - **Subdomain** (e.g. `standings.example.com`): a `CNAME` record
     pointing to `<username>.github.io`.
   - **Apex/root domain** (e.g. `example.com`): four `A` records
     pointing at GitHub Pages' IPs:
     ```
     185.199.108.153
     185.199.109.153
     185.199.110.153
     185.199.111.153
     ```
     (Some providers offer `ALIAS`/`ANAME` records instead of `A` records
     for apex domains — use those if available.)
4. Back in **Settings → Pages**, enter your custom domain under
   **Custom domain** and save. Optionally check **Enforce HTTPS** once
   GitHub provisions a certificate (can take up to 24 hours after DNS
   propagates).
5. DNS changes can take anywhere from a few minutes to 48 hours to
   propagate; GitHub's Pages settings page will show a green check once
   it can verify your domain.
