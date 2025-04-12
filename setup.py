import os
import sys
import json
import glob
from pathlib import Path

def create_symlinks(source_dir, target_dir):
    """Create file symlinks while maintaining real directories"""
    print(f"\nProcessing source: {source_dir}")
    print(f"Target directory: {target_dir}")

    for root, dirs, files in os.walk(source_dir):
        # Create relative path from source directory
        rel_path = os.path.relpath(root, source_dir)
        target_root = os.path.join(target_dir, rel_path)

        # Create real directories in target
        Path(target_root).mkdir(parents=True, exist_ok=True)

        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_root, file)

            # Skip special files
            if file in ['.gitkeep', '.gitignore']:
                continue

            # Remove existing file/symlink if needed
            if os.path.lexists(target_file):
                if os.path.islink(target_file) or os.path.isfile(target_file):
                    print(f"Replacing: {target_file}")
                    os.remove(target_file)
                else:
                    print(f"Skipping directory: {target_file}")
                    continue

            try:
                print(f"Linking: {target_file} -> {source_file}")
                os.symlink(os.path.abspath(source_file), target_file)
            except OSError as e:
                print(f"Error creating symlink: {e}", file=sys.stderr)

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
        if not os.path.exists(source_src):
            print(f"\nSkipping {os.path.basename(source)} - no src directory")
            continue

        print(f"\n{'=' * 40}")
        print(f"Processing: {os.path.basename(source)}/src")
        create_symlinks(source_src, parent_dir)

    # Update community plugins list
    update_community_plugins(parent_dir, obsidian_sources)

    print("\nSetup complete. Git-friendly links created in:", parent_dir)

if __name__ == "__main__":
    main()