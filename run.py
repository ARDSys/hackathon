import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# FILENAME = "Autoimmunity.json"
# FILENAME = "BTK_Inhibitors.json"
FILENAME = "Novel_Therapeutic_Approaches.json"

from src.master import Master


if __name__ == "__main__":
    master = Master(FILENAME)
    master.run()
