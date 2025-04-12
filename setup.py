import os
import sys
import json
import glob

def create_symlinks(source_dir, target_dir):
    """Recursively create symbolic links from source to target directory."""
    print(f"\nProcessing source: {source_dir}")
    print(f"Target directory: {target_dir}")

    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)

    try:
        items = os.listdir(source_dir)
    except FileNotFoundError:
        print(f"Source directory not found: {source_dir}", file=sys.stderr)
        return

    for item_name in items:
        source_item = os.path.join(source_dir, item_name)
        target_item = os.path.join(target_dir, item_name)

        source_abs = os.path.abspath(source_item)
        target_abs = os.path.abspath(target_item)

        # Skip self-referential links
        if os.path.commonpath([source_abs]) == os.path.commonpath([source_abs, target_abs]):
            print(f"Skipping self-referential path: {source_abs}")
            continue

        # Handle existing target items
        if os.path.lexists(target_abs):
            if os.path.islink(target_abs) or os.path.isfile(target_abs):
                print(f"Replacing existing item: {target_abs}")
                os.remove(target_abs)
            elif os.path.isdir(target_abs):
                if os.path.isdir(source_abs):
                    print(f"Merging into directory: {target_abs}")
                    create_symlinks(source_abs, target_abs)
                continue
            else:
                print(f"Skipping unknown item type: {target_abs}")
                continue

        # Create new symlink or directory
        if os.path.isdir(source_abs):
            print(f"Creating directory symlink: {target_abs} -> {source_abs}")
            os.symlink(source_abs, target_abs, target_is_directory=True)
        else:
            print(f"Creating file symlink: {target_abs} -> {source_abs}")
            os.symlink(source_abs, target_abs)

def update_community_plugins(parent_dir, obsidian_sources):
    """Update community-plugins.json in parent directory with all plugins"""
    json_path = os.path.join(parent_dir, "community-plugins.json")
    
    all_plugins = []
    for source in obsidian_sources:
        plugins_dir = os.path.join(source, "src", "plugins")
        if os.path.exists(plugins_dir):
            try:
                plugins = [d for d in os.listdir(plugins_dir) 
                          if os.path.isdir(os.path.join(plugins_dir, d))]
                all_plugins.extend(plugins)
            except OSError as e:
                print(f"Error reading plugins from {plugins_dir}: {e}", file=sys.stderr)

    existing_plugins = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                existing_plugins = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading community-plugins.json: {e}", file=sys.stderr)

    merged_plugins = sorted(list(set(existing_plugins + all_plugins)))

    if existing_plugins != merged_plugins:
        try:
            with open(json_path, "w") as f:
                json.dump(merged_plugins, f, indent=4)
            print(f"Updated community-plugins.json with {len(all_plugins)} new plugins")
        except IOError as e:
            print(f"Error writing community-plugins.json: {e}", file=sys.stderr)
    else:
        print("community-plugins.json already up-to-date")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    obsidian_sources = glob.glob(os.path.join(parent_dir, "*.obsidian"))
    obsidian_sources = [f for f in obsidian_sources if os.path.isdir(f)]

    if not obsidian_sources:
        print(f"No *.obsidian folders found in {parent_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(obsidian_sources)} configuration sources:")
    for source in obsidian_sources:
        print(f" - {os.path.basename(source)}")

    # First pass: Create all directory structures
    for source in obsidian_sources:
        source_src = os.path.join(source, "src")
        if not os.path.exists(source_src):
            print(f"\nSkipping {os.path.basename(source)} - no src directory found")
            continue

        print(f"\n{'=' * 40}")
        print(f"Processing source: {os.path.basename(source)}/src")
        create_symlinks(source_src, parent_dir)

    # Update community plugins list
    update_community_plugins(parent_dir, obsidian_sources)

    print("\nSetup complete. Configuration merged to:", parent_dir)

if __name__ == "__main__":
    main()