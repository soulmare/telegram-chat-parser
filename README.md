## Install dependencies
```bash
sudo apt install -y python3-venv
python3 -m venv venv
source venv/bin/activate
pip install matplotlib pandas
```

## TODO
- User Activity Heatmap
- Bubble Chart: User Participation Overview
  - Each bubble = one user
  - X-axis: Messages sent
  - Y-axis: Reactions received
  - Bubble size: Average message length
