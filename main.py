import sys
import os
import zlib
import hashlib

def get_tree_entries(tree_sha):
    with open(f".git/objects/{tree_sha[:2]}/{tree_sha[2:]}", "rb") as f:
        tree_content = f.read()
        decompressed_content = zlib.decompress(tree_content)
        header_index = decompressed_content.find(b"\0")
        actual_content = decompressed_content[header_index + 1 :]
        actual_content = actual_content.split(b" ")
        mode = actual_content[0]
        entries = []
        for e in range(1, len(actual_content[1:]) + 1):
            x = actual_content[e].split(b"\0")
            name = x[0]
            sha = x[1][:20]
            entry = {
                "mode": mode.decode("utf-8"),
                "name": name.decode("utf-8"),
                "sha": sha.hex(),
                "type": "tree"
                if mode.decode("utf-8") in ("040000", "40000")
                else "blob",
            }
            entries.append(entry)
            mode = x[1][20:]
    return entries

def hash_object(data, obj_type="blob", write=True):
    header = f"{obj_type} {len(data)}\0"
    full_data = header.encode() + data
    sha1 = hashlib.sha1(full_data).hexdigest()
    if write:
        # Ensure the directory for the first two characters of the SHA-1 exists
        dir_path = f".git/objects/{sha1[:2]}"
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        # Write the object file
        with open(f"{dir_path}/{sha1[2:]}", "wb") as f:
            f.write(zlib.compress(full_data))

    return sha1

def write_tree(current_directory):
    entries = []
    # List all files and directories in the current directory
    all_files_dirs = os.listdir(current_directory)
    for entry in sorted(all_files_dirs):
        # Skip the .git directory
        if entry == ".git":
            continue
        path = os.path.join(current_directory, entry)
        if os.path.isdir(path):
            # Recursively write tree for subdirectory
            sha1 = write_tree(path)
            mode = "40000"  # Directory mode
        else:
            with open(path, "rb") as f:
                data = f.read()
            sha1 = hash_object(data)
            mode = "100644"  # File mode
        entries.append(f"{mode} {entry}\0".encode() + bytes.fromhex(sha1))
    tree_data = b"".join(entries) 

    return hash_object(tree_data, "tree")

def create_commit(tree,parent,message=""):
    commit_data = f"tree {tree}\nparent {parent}\nauthor BouraouiChifour bouraoui404@gmail.com\nauthor BouraouiChifour bouraoui404@gmail.com\n\n{message}\n".encode() 
    commit_sha = hash_object(commit_data,"commit")
    return commit_sha

def clone_repo(url):
    '''
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")'''

def main():
    if len(sys.argv) == 1:
        print("no arguments provided")

    else:
        command = sys.argv[1]
        if command == "init":
            os.mkdir(".git")
            os.mkdir(".git/objects")
            os.mkdir(".git/refs")
            with open(".git/HEAD", "w") as f:
                f.write("ref: refs/heads/main\n")
            print("Initialized git directory")

        elif command == "cat-file":
            if sys.argv[2] == "-p":
                blob_sha = sys.argv[3]
                blob_path = ".git/objects/" + blob_sha[:2] + "/" + blob_sha[2:]
                with open(blob_path, "rb") as f:
                    blob_content = f.read()
                    decompressed_content = zlib.decompress(blob_content)
                    decompressed_str = decompressed_content.decode("utf-8")
                    print(decompressed_str.split("\0")[1], end="")

        elif command == "hash-object":
            if sys.argv[2] == "-w":
                with open(sys.argv[3],"rb") as f:
                    data = f.read()
                    blob_hash = hash_object(data)
                    print(blob_hash)

        elif command == "ls-tree":
            if sys.argv[2] == "--name-only":
                tree_sha = sys.argv[3]
                entries = get_tree_entries(tree_sha)
                for entry in entries:
                    print(entry["name"])
            else:
                tree_sha = sys.argv[2]
                entries = get_tree_entries(tree_sha)
                for entry in entries:
                    print(
                        f'{entry["mode"]} {entry["type"]} {entry["sha"]} {entry["name"]}'
                    )

        elif command == "write-tree":
            print(write_tree(os.getcwd()))

        elif command == "commit-tree":
            tree_sha = sys.argv[2]
            if sys.argv[3] == "-p":
                parent_sha = sys.argv[4]
                if sys.argv[5] == "-m":
                    commit_msg = sys.argv[6]
                    print(create_commit(tree_sha,parent_sha,commit_msg))
        
        elif command == "clone":
            repo_url = sys.argv[2]
            destination_dir = sys.argv[3]
            os.mkdir(destination_dir)
            os.chdir(destination_dir)
            clone_repo(repo_url)

        else:
            raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
