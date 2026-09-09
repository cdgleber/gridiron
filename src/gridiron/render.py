from __future__ import annotations

from datetime import datetime

from jinja2 import Environment

from gridiron.scoring import BetterRow, TeamRow

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NFL Pool Standings</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f172a; color: #e2e8f0; padding: 24px; }
  .container { max-width: 1100px; margin: 0 auto; }
  h1 { font-size: 1.8rem; margin-bottom: 4px; }
  .updated { color: #94a3b8; font-size: 0.85rem; margin-bottom: 24px; }
  .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 24px; }
  h2 { font-size: 1.2rem; margin-bottom: 12px; }
  input.search { padding: 8px 14px; border-radius: 8px; border: 1px solid #334155;
                 background: #0f172a; color: #e2e8f0; margin-bottom: 12px; width: 100%; max-width: 320px; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; padding: 10px; cursor: pointer; background: #334155;
       position: sticky; top: 0; }
  th:first-child { border-top-left-radius: 8px; }
  th:last-child { border-top-right-radius: 8px; }
  td { padding: 10px; border-bottom: 1px solid #334155; }
  img.logo { max-width: 28px; height: auto; }
  .better-link { color: #38bdf8; cursor: pointer; }
  .better-link:hover { text-decoration: underline; }
  .active-filter { color: #f472b6; font-weight: 700; }
</style>
</head>
<body>
<div class="container">
  <h1>NFL Pool Standings</h1>
  <div class="updated">Season {{ season }} &middot; Updated: {{ generated_at }}</div>

  <div class="card">
    <h2>Leaderboard</h2>
    <input class="search" id="searchBetters" placeholder="Search betters...">
    <table id="betters">
      <thead>
        <tr>
          <th onclick="sortTable('betters', 0)">Better</th>
          <th onclick="sortTable('betters', 1)">Score</th>
          <th onclick="sortTable('betters', 2)">Wins</th>
          <th onclick="sortTable('betters', 3)">Losses</th>
          <th onclick="sortTable('betters', 4)">Div Losses</th>
          <th onclick="sortTable('betters', 5)">Games Played</th>
        </tr>
      </thead>
      <tbody>
        {% for row in better_rows %}
        <tr>
          <td>{{ row.name }}</td>
          <td>{{ row.score }}</td>
          <td>{{ row.wins }}</td>
          <td>{{ row.losses }}</td>
          <td>{{ row.division_losses }}</td>
          <td>{{ row.games_played }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Teams</h2>
    <input class="search" id="searchTeams" placeholder="Search teams...">
    <table id="teams">
      <thead>
        <tr>
          <th></th>
          <th onclick="sortTable('teams', 1)">Team</th>
          <th onclick="sortTable('teams', 2)">Score</th>
          <th onclick="sortTable('teams', 3)">Wins</th>
          <th onclick="sortTable('teams', 4)">Losses</th>
          <th onclick="sortTable('teams', 5)">Div Losses</th>
          <th onclick="sortTable('teams', 6)">Games Played</th>
          <th>Betters</th>
        </tr>
      </thead>
      <tbody>
        {% for row in team_rows %}
        <tr>
          <td><img class="logo" src="{{ row.logo_url }}" alt=""></td>
          <td>{{ row.name }}</td>
          <td>{{ row.score }}</td>
          <td>{{ row.wins }}</td>
          <td>{{ row.losses }}</td>
          <td>{{ row.division_losses }}</td>
          <td>{{ row.games_played }}</td>
          <td>
            {% for picker in row.pickers %}<span class="better-link" onclick="filterByBetter('{{ picker }}')">{{ picker }}</span>{% if not loop.last %}, {% endif %}{% endfor %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
function sortTable(tableId, columnIndex) {
  const table = document.getElementById(tableId);
  const rows = Array.from(table.tBodies[0].rows);
  const numeric = columnIndex > 0;
  const current = table.dataset.sortCol === String(columnIndex) ? table.dataset.sortDir : "desc";
  const dir = current === "asc" ? "desc" : "asc";
  rows.sort((a, b) => {
    let x = a.cells[columnIndex].innerText.trim();
    let y = b.cells[columnIndex].innerText.trim();
    if (numeric) { x = parseFloat(x) || 0; y = parseFloat(y) || 0; }
    if (x < y) return dir === "asc" ? -1 : 1;
    if (x > y) return dir === "asc" ? 1 : -1;
    return 0;
  });
  rows.forEach(row => table.tBodies[0].appendChild(row));
  table.dataset.sortCol = String(columnIndex);
  table.dataset.sortDir = dir;
}

function filterByBetter(name) {
  const rows = document.getElementById("teams").tBodies[0].rows;
  for (const row of rows) {
    row.style.display = row.cells[7].innerText.includes(name) ? "" : "none";
  }
  document.querySelectorAll(".better-link").forEach(el => {
    el.classList.toggle("active-filter", el.textContent === name);
  });
}

function wireSearch(inputId, tableId, columnIndex) {
  document.getElementById(inputId).addEventListener("input", (e) => {
    const filter = e.target.value.toLowerCase();
    const rows = document.getElementById(tableId).tBodies[0].rows;
    for (const row of rows) {
      const text = row.cells[columnIndex].innerText.toLowerCase();
      row.style.display = text.includes(filter) ? "" : "none";
    }
  });
}

wireSearch("searchBetters", "betters", 0);
wireSearch("searchTeams", "teams", 1);
</script>
</body>
</html>
"""

_env = Environment(autoescape=True)
_template = _env.from_string(_TEMPLATE)


def render_page(
    better_rows: list[BetterRow],
    team_rows: list[TeamRow],
    season: int,
    generated_at: datetime,
) -> str:
    return _template.render(
        better_rows=better_rows,
        team_rows=team_rows,
        season=season,
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
    )
