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
```

## TODO
- User Activity Heatmap
- Bubble Chart: User Participation Overview
  - Each bubble = one user
  - X-axis: Messages sent
  - Y-axis: Reactions received
  - Bubble size: Average message length
