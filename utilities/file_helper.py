import os
import stat
import ctypes
from pathlib import Path
from sys import path

# Writes a list to a file
def write_list_to_new_file(file_name, list=[]):
    # check if file already exists
    
    if os.path.exists(file_name):
        raise FileExistsError(f"File {file_name} already exists.")

    with open(file_name, "w") as f:
        for line in list:
            f.write(line)
            f.write("\n")

def write_dict_to_new_file(file_name, data):
    import json

    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)

    return

def create_dict_from_file(file_name):
    import json

    with open(file_name, 'r') as file:
        return json.load(file) 

# Adds a list to a file, creates one if needed
def add_list_to_file(file_name, list=[]):
    with open(file_name, "a") as f:
        for line in list:
            f.write(line)
            f.write("\n")

# Delete a file, hard delete even thumbs.db
def delete_file(file_name):
    try:
        os.remove(file_name)
    except PermissionError:
        # If it's a Thumbs.db file, attempt to force delete it
        if os.path.basename(file_name).lower() == "thumbs.db":
            force_delete_thumbs_db(os.path.dirname(file_name))
        else:
            raise
    except FileNotFoundError:
        # If the file doesn't exist, we can ignore this error
        pass
    except IsADirectoryError:
        # If it's a directory, we can ignore this error
        pass

# Delete stubborn thumbs.db files.
def force_delete_thumbs_db(root_dir):
    """
    Recursively finds and hard-deletes Thumbs.db files,
    handling hidden attributes and active process locks.
    """
    # MoveFileEx flag to delete file on next system reboot
    MOVEFILE_DELAY_UNTIL_REBOOT = 0x00000004
    
    for path in Path(root_dir).rglob('*'):
        # Target both exact casing and lowercase variations
        if path.is_file() and path.name.lower() == 'thumbs.db':
            str_path = str(path)
            try:
                print(f"Targeting: {str_path}")
                
                # 1. Clear Read-Only, Hidden, and System attributes
                os.chmod(str_path, stat.S_IWRITE)
                if os.name == 'nt':  # Windows-specific attribute removal
                    ctypes.windll.kernel32.SetFileAttributesW(str_path, stat.S_IWRITE)
                
                # 2. Attempt immediate hard deletion
                os.remove(str_path)
                print(f"Successfully deleted: {str_path}")
                
            except PermissionError:
                # 3. Handle active process locks (e.g., Windows Explorer)
                print(f"File locked: {str_path}. Scheduling deletion for next reboot.")
                if os.name == 'nt':
                    success = ctypes.windll.kernel32.MoveFileExW(
                        str_path, None, MOVEFILE_DELAY_UNTIL_REBOOT
                    )
                    if not success:
                        print(f"Failed to schedule reboot deletion for {str_path}")
                else:
                    print("Reboot scheduling is only supported on Windows.")
            except Exception as e:
                print(f"Error processing {str_path}: {e}")

def open_file_in_notepad(file_path):
    import subprocess
    subprocess.Popen(["notepad.exe", file_path])
