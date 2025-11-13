import json

with open("design-docs/spaces.json", "r") as f:
    data = json.load(f)

    archived_space_keys = []

    for space in data.get("results", []):
        if space.get("status") == "archived":
            archived_space_keys.append(space.get("key"))

    print(archived_space_keys)