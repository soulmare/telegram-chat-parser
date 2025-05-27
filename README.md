## Install dependencies
```bash
sudo apt install -y python3-venv
python3 -m venv venv
source venv/bin/activate
pip install networkx matplotlib pandas
```

## Usage
```bash
python3 users_counts_graph.py --period month --begin '2024-06-01' --min 1000 --include-others --output data/chart.png data/2025-04-04-AA.json
python3 users_counts_log.py --period month --begin '2025-01-01' --min 900 --include-others data/2025-04-04-AA.json > data/users_messages_grouped_counts.csv
python3 messages_to_csv.py data/2025-26-04_14-05-AA.json > data/2025-26-04_14-05-AA.csv
python3 replies_graph.py --output data/replies_graph-2025-05-24-AA.png --min-replies 17 --from-date '2025-05-15' --nick user870252229:"Hiro" --nick user401097156:"Alyssa Le-Ko" --nick user332752680:"Кусь Кусь" --nick user6108164014:"Марсіянський\nчерв'як" --nick user592650086:"Sofiia\nBaidiuk-Popova" --nick user784813495:"Valeriia\nShapovalova" data/2025-05-24-AA.csv
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
