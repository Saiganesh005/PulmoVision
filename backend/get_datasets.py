import json
from download_dataset import DATASETS

def main() -> None:
    # Just return the dataset names and handles, not the paths, as paths require downloading
    print(json.dumps(DATASETS))

if __name__ == "__main__":
    main()
