import os
import sys
import json
import glob
from pathlib import Path

def create_relative_symlink(source, target):
    """Create relative symlinks that work across systems"""
    source_path = Path(source).resolve()
    target_path = Path(target).resolve()

    # Ensure target directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate relative path from target to source
    try:
        rel_path = os.path.relpath(source_path, target_path.parent)
    except ValueError:
        # Handle different drive letters on Windows
        print(f"Can't create relative link between different drives: {source} -> {target}")
        return

    # Remove existing target if it's not our symlink
    if target_path.exists():
        os.remove(target_path)

    # Create the symlink
    os.symlink(rel_path, target_path)

def create_symlinks(source_dir, target_dir):
    """Create proper relative symlinks maintaining structure"""
    for root, _, files in os.walk(source_dir):
        for file in files:
            source_file = Path(root) / file
            target_file = Path(target_dir) / source_file.relative_to(source_dir)

            rel_path = os.path.relpath(source_file, target_file.parent)
            if target_file.is_symlink() and os.readlink(target_file) == rel_path:
                continue

            print(f"Linking: {target_file} -> {source_file}")
            create_relative_symlink(source_file, target_file)

def update_community_plugins(parent_dir, obsidian_sources):
    """Update community-plugins.json with plugin directory names"""
    json_path = os.path.join(parent_dir, "community-plugins.json")

    plugin_dirs = set()
    for source in obsidian_sources:
        plugins_path = os.path.join(source, "src", "plugins")
        if os.path.exists(plugins_path):
            try:
                plugins = [d for d in os.listdir(plugins_path)
                          if os.path.isdir(os.path.join(plugins_path, d))]
                plugin_dirs.update(plugins)
            except OSError as e:
                print(f"Error reading plugins: {e}", file=sys.stderr)

    existing_plugins = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                existing_plugins = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading plugins list: {e}", file=sys.stderr)

    merged_plugins = sorted(list(plugin_dirs.union(existing_plugins)))

    if existing_plugins != merged_plugins:
        try:
            with open(json_path, "w") as f:
                json.dump(merged_plugins, f, indent=4)
            print(f"Updated community-plugins.json with {len(merged_plugins)} plugins")
        except IOError as e:
            print(f"Error writing plugins list: {e}", file=sys.stderr)
    else:
        print("community-plugins.json unchanged")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)

    obsidian_sources = glob.glob(os.path.join(parent_dir, "*.obsidian"))
    obsidian_sources = [f for f in obsidian_sources if os.path.isdir(f)]

    if not obsidian_sources:
        print("No *.obsidian folders found", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(obsidian_sources)} configuration sources:")
    for source in obsidian_sources:
        print(f" - {os.path.basename(source)}")

    # Process each source
    for source in obsidian_sources:
        source_src = os.path.join(source, "src")
        content_src = os.path.join(source, "content")
        obsidian = os.path.basename(source)

        if not os.path.exists(source_src):
            print(f"\nSkipping {obsidian} - no src directory")
            continue

        print(f"\n{'=' * 40}")

        print(f"Processing: {obsidian}/src")
        create_symlinks(source_src, parent_dir)

        print(f"Processing: {obsidian}/content")
        create_symlinks(content_src, Path(parent_dir).resolve().parent)

    # Update community plugins list
    update_community_plugins(parent_dir, obsidian_sources)

    print("\nSetup complete. Git-friendly links created in:", parent_dir)

if __name__ == "__main__":
    main()