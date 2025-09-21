✨ Features

🔹 Core File & Directory Commands

    ls [path] → List directory contents.
    cd [path] → Change directory (defaults to home if no path is given).
    pwd → Print the current working directory.
    mkdir ... → Create one or more directories.
    rm <file/dir>... → Remove files or directories (recursively for folders).

🔹 System Utilities

    monitor → Show CPU load (1-minute average) and memory usage.
    help → Display all supported commands.
    exit → Exit the terminal.

🔹 Advanced Features

    run <script> → Run Python scripts (.py) or executables in the current directory.

    schedule at → Schedule when a task should be done

    weather api (OpenWeatherMap)

    ai → Execute tasks using plain English, such as:
        create folder test
        move file.txt to documents
        remove temp
        list files in downloads

🔹 Cross-Platform Support

    Works on Linux, macOS, and Windows (though memory/CPU info is limited on Windows).

Example Usage

bash $ pwd /home/user/projects

$ mkdir test_folder Directory 'test_folder' created.

$ ls terminal.py test_folder

$ ai create folder notes Folder 'notes' created.

$ monitor CPU Load (1 min average): 0.35 Memory Usage: 1200 MB used of 8000 MB total


🛠️ Acknowledgments

While developing this project, I utilized the CodeMate VS Code Extension to assist with 
error detection and code optimization. I was amazed by how helpful it was and how much 
easier it made for me to write clean, error-free code. It provided valuable insights that
helped me refine my code, ensuring better performance and reliability.
