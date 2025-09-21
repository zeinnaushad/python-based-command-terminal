import os
import sys
import shutil
import subprocess
import psutil
import re
import threading
import time
import requests
import schedule
from datetime import datetime


if sys.platform == 'win32':
    try:
        import pyreadline as readline
        readline = None
    except ImportError:
        print("pyreadline is required on Windows for command history and tab completion.")
        print("Install it with: pip install pyreadline")
        sys.exit(1)
else:
    import readline
    readline.parse_and_bind("tab: complete")

from rich.console import Console
from rich.text import Text
from rich.progress import BarColumn, Progress, TextColumn
from rich.style import Style

console = Console()

COMMANDS = ['ls', 'cd', 'pwd', 'mkdir', 'rm', 'exit', 'help', 'monitor', 'ai', 'run', 'schedule', 'fetch']

def print_error(message):
    console.print(f"Error: {message}", style="bold red")

def get_line_buffer_safe():
    if readline and hasattr(readline, 'get_line_buffer'):
        return readline.get_line_buffer()
    else:
        return ''

def completer(text, state):
    buffer = get_line_buffer_safe()
    line = buffer.split()

    if len(line) == 0 or (len(line) == 1 and not buffer.endswith(' ')):
        options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    else:
        try:
            dir_path = '.'
            sep = os.path.sep
            altsep = os.path.altsep if os.path.altsep else ''
            if sep in text or (altsep and altsep in text):
                norm_text = text.replace(altsep, sep) if altsep else text
                dir_path = os.path.dirname(norm_text)
                text = os.path.basename(norm_text)
                if dir_path == '':
                    dir_path = '.'
            files = os.listdir(dir_path)
            options = [f for f in files if f.startswith(text)]
            options = [os.path.join(dir_path, f) if dir_path != '.' else f for f in options]
        except Exception:
            options = []
    try:
        return options[state]
    except IndexError:
        return None

if readline and hasattr(readline, 'set_completer'):
    readline.set_completer(completer)
    if sys.platform != 'win32':
        readline.parse_and_bind("tab: complete")

def cmd_ls(args):
    path = args[0] if args else '.'
    try:
        files = os.listdir(path)
        files.sort()
        for f in files:
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path):
                console.print(f, style="bold blue")
            else:
                console.print(f)
    except FileNotFoundError:
        print_error(f"ls: cannot access '{path}': No such file or directory")
    except NotADirectoryError:
        print_error(f"ls: cannot access '{path}': Not a directory")
    except PermissionError:
        print_error(f"ls: cannot open directory '{path}': Permission denied")

def cmd_cd(args):
    if not args:
        target = os.path.expanduser('~')
    else:
        target = args[0]
    try:
        os.chdir(target)
    except FileNotFoundError:
        print_error(f"cd: no such file or directory: {target}")
    except NotADirectoryError:
        print_error(f"cd: not a directory: {target}")
    except PermissionError:
        print_error(f"cd: permission denied: {target}")

def cmd_pwd(args):
    console.print(os.getcwd(), style="bold green")

def cmd_mkdir(args):
    if not args:
        print_error("mkdir: missing operand")
        return
    for directory in args:
        try:
            os.mkdir(directory)
            console.print(f"Directory '{directory}' created.", style="green")
        except FileExistsError:
            print_error(f"mkdir: cannot create directory '{directory}': File exists")
        except PermissionError:
            print_error(f"mkdir: cannot create directory '{directory}': Permission denied")
        except OSError as e:
            print_error(f"mkdir: cannot create directory '{directory}': {e}")

def cmd_rm(args):
    if not args:
        print_error("rm: missing operand")
        return
    for target in args:
        if not os.path.exists(target):
            print_error(f"rm: cannot remove '{target}': No such file or directory")
            continue
        try:
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
            console.print(f"Removed '{target}'.", style="green")
        except PermissionError:
            print_error(f"rm: cannot remove '{target}': Permission denied")
        except OSError as e:
            print_error(f"rm: cannot remove '{target}': {e}")

def cmd_help(args):
    console.print("Supported commands:", style="bold underline")
    console.print("  ls [path]       - list directory contents")
    console.print("  cd [path]       - change directory")
    console.print("  pwd             - print current directory")
    console.print("  mkdir <dir>...  - create directories")
    console.print("  rm <file/dir>...- remove files or directories")
    console.print("  monitor         - show CPU and memory usage")
    console.print("  ai <natural language command> - execute natural language commands")
    console.print("  run <script>    - run Python, shell scripts (Unix), or executables")
    console.print("  schedule <command> at HH:MM - schedule a command to run daily at specified time")
    console.print("  fetch <query>   - fetch info from web APIs (e.g. weather)")
    console.print("  exit            - exit the terminal")
    console.print("  help            - show this help message")

def cmd_monitor(args):
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()

    console.print("[bold]CPU Usage:[/bold]")
    with Progress(
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(bar_width=40, complete_style=Style(color="cyan")),
        transient=True,
    ) as progress:
        task = progress.add_task("CPU", total=100)
        progress.update(task, completed=cpu_percent)
        progress.refresh()
    console.print(f"{cpu_percent:.1f}%")

    console.print("[bold]Memory Usage:[/bold]")
    with Progress(
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(bar_width=40, complete_style=Style(color="magenta")),
        transient=True,
    ) as progress:
        task = progress.add_task("Memory", total=100)
        progress.update(task, completed=mem.percent)
        progress.refresh()
    console.print(f"{mem.percent:.1f}% ({mem.used // (1024**2)} MB used of {mem.total // (1024**2)} MB)")

def parse_natural_language(command):
    command = command.lower()

    m = re.match(r'.*create (a )?(folder|directory) (\S+)', command)
    if m:
        folder_name = m.group(3)
        try:
            os.mkdir(folder_name)
            console.print(f"Folder '{folder_name}' created.", style="green")
        except FileExistsError:
            print_error(f"Folder '{folder_name}' already exists.")
        except Exception as e:
            print_error(f"Error creating folder '{folder_name}': {e}")
        return

    m = re.match(r'.*move (\S+) (to|into) (\S+)', command)
    if m:
        src = m.group(1)
        dst = m.group(3)
        if not os.path.exists(src):
            print_error(f"Source file '{src}' does not exist.")
            return
        if not os.path.exists(dst):
            print_error(f"Destination folder '{dst}' does not exist.")
            return
        if not os.path.isdir(dst):
            print_error(f"Destination '{dst}' is not a folder.")
            return
        try:
            shutil.move(src, dst)
            console.print(f"Moved '{src}' to '{dst}'.", style="green")
        except Exception as e:
            print_error(f"Error moving file: {e}")
        return

    m = re.match(r'.*remove (\S+)', command)
    if m:
        target = m.group(1)
        if not os.path.exists(target):
            print_error(f"'{target}' does not exist.")
            return
        try:
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
            console.print(f"Removed '{target}'.", style="green")
        except Exception as e:
            print_error(f"Error removing '{target}': {e}")
        return

    m = re.match(r'.*list files in (\S+)', command)
    if m:
        folder = m.group(1)
        if not os.path.exists(folder):
            print_error(f"Folder '{folder}' does not exist.")
            return
        if not os.path.isdir(folder):
            print_error(f"'{folder}' is not a folder.")
            return
        try:
            files = os.listdir(folder)
            console.print(f"Files in '{folder}':", style="bold")
            for f in files:
                console.print(f)
        except Exception as e:
            print_error(f"Error listing files: {e}")
        return

    print_error("Sorry, I could not understand the command.")

def cmd_ai(args):
    if not args:
        print_error("ai: missing natural language command")
        return
    command = ' '.join(args)
    parse_natural_language(command)


def cmd_run(args):
    if not args:
        print_error("run: missing script or executable name")
        return
    target = args[0]
    if not os.path.exists(target):
        print_error(f"run: '{target}' does not exist")
        return

    ext = os.path.splitext(target)[1].lower()
    try:
        if ext == '.py':
            result = subprocess.run([sys.executable, target] + args[1:], text=True, capture_output=True)
        elif ext == '.sh':
            if sys.platform == 'win32':
                print_error("run: shell scripts are not supported on Windows")
                return
            result = subprocess.run(['bash', target] + args[1:], text=True, capture_output=True)
        elif os.access(target, os.X_OK):
            result = subprocess.run([target] + args[1:], text=True, capture_output=True)
        else:
            print_error(f"run: cannot execute '{target}' (unsupported file type or not executable)")
            return

        if result.stdout:
            console.print(result.stdout, end='')
        if result.stderr:
            console.print(result.stderr, style="red", end='')
    except Exception as e:
        print_error(f"run: error running '{target}': {e}")


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

def dispatch_command(cmd, args):
    if cmd == 'exit':
        sys.exit(0)
    elif cmd == 'ls':
        cmd_ls(args)
    elif cmd == 'cd':
        cmd_cd(args)
    elif cmd == 'pwd':
        cmd_pwd(args)
    elif cmd == 'mkdir':
        cmd_mkdir(args)
    elif cmd == 'rm':
        cmd_rm(args)
    elif cmd == 'help':
        cmd_help(args)
    elif cmd == 'monitor':
        cmd_monitor(args)
    elif cmd == 'ai':
        cmd_ai(args)
    elif cmd == 'run':
        cmd_run(args)
    elif cmd == 'schedule':
        cmd_schedule(args)
    elif cmd == 'fetch':
        cmd_fetch(args)
    else:
        try:
            result = subprocess.run([cmd] + args, check=False, text=True, capture_output=True)
            if result.stdout:
                console.print(result.stdout, end='')
            if result.stderr:
                console.print(result.stderr, style="red", end='')
        except FileNotFoundError:
            print_error(f"{cmd}: command not found")
        except Exception as e:
            print_error(f"Error running command '{cmd}': {e}")

def cmd_schedule(args):
    if len(args) < 3:
        print_error("schedule: usage: schedule <command...> at HH:MM")
        return
    try:
        at_index = args.index('at')
    except ValueError:
        print_error("schedule: missing 'at' keyword")
        return

    command = args[:at_index]
    time_str = args[at_index + 1] if len(args) > at_index + 1 else None
    if not time_str:
        print_error("schedule: missing time after 'at'")
        return

    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        print_error("schedule: time must be in HH:MM format")
        return

    def job():
        console.print(f"[bold green]Scheduled job running:[/bold green] {' '.join(command)}")
        dispatch_command(command[0], command[1:])

    schedule.every().day.at(time_str).do(job)
    console.print(f"Scheduled command '{' '.join(command)}' at {time_str}")


OPENWEATHER_API_KEY = "YOUR_API_KEY_HERE"  # you could go to openweather and subscribe to their api and paste that key here

def cmd_fetch(args):
    if not args:
        print_error("fetch: missing query")
        return
    query = ' '.join(args).lower()

    m = re.match(r'weather in (.+)', query)
    if m:
        city = m.group(1)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        try:
            resp = requests.get(url)
            data = resp.json()
            if data.get('cod') != 200:
                print_error(f"fetch: city '{city}' not found")
                return
            weather = data['weather'][0]['description']
            temp = data['main']['temp']
            console.print(f"Weather in {city.title()}: {weather}, Temperature: {temp}°C", style="bold cyan")
        except Exception as e:
            print_error(f"fetch: error fetching weather: {e}")
        return

    print_error("fetch: unsupported query")

def main():
    while True:
        try:
            cwd = os.getcwd()
            prompt_text = Text(f"{cwd} $ ", style="bold green")
            inp = console.input(prompt_text).strip()
            if not inp:
                continue
            parts = inp.split()
            cmd, args = parts[0], parts[1:]
            dispatch_command(cmd, args)

        except KeyboardInterrupt:
            console.print()  # Newline on Ctrl+C
        except EOFError:
            console.print()  # Newline on Ctrl+D
            break

if __name__ == "__main__":
    main()
