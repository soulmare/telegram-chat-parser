## Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
# Two-step process of building a replies graph
python3 messages_to_replies_data.py data/2025-09-27_2025-11-13-AA.json --nickname-file data/nicknames.txt --mirror --min-replies 25 --min-count-perc 10 > data/2025-09-27_2025-11-13-AA.replies_data.csv
python3 replies_graph.py data/2025-09-27_2025-11-13-AA.replies_data.csv --from-id-field user1_id --from-name-field user1_name --reply-id-field user2_id --reply-name-field user2_name --weight-field messages_count --layout-k 8.0

# Other tools
python3 users_counts_graph.py --period month --begin '2024-06-01' --min 1000 --include-others --output data/chart.png data/2025-04-04-AA.json
python3 users_counts_log.py --period month --begin '2025-01-01' --min 900 --include-others data/2025-04-04-AA.json > data/users_messages_grouped_counts.csv
python3 count_by_timeperiod.py week data/2026-01-22-AA.all.json > data/2026-01-22-AA.all.stats_weekly.csv
```

## JQ
```bash
# Extract polls as JSON
jq '.messages[] 
  | select(.poll and (.forwarded_from | not)) 
  | {question: .poll.question, from, date, total_voters: .poll.total_voters}' data/2025-05-24-AA.json data/2025-05-24-AA.json
# Polls list flat
jq -r '.messages[] | select(.poll and (.forwarded_from | not)) | .poll.question' data/2025-05-24-AA.json
```

## TODO
- User Activity Heatmap
- Bubble Chart: User Participation Overview
  - Each bubble = one user
  - X-axis: Messages sent
  - Y-axis: Reactions received
  - Bubble size: Average message length
