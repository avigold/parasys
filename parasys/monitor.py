import sys
import psutil
import time
try:
    import curses
except ImportError:
    if sys.platform.startswith('win'):
        try:
            import windows_curses as curses # might as well support windows
        except ImportError:
            print("The curses module is required to run parasys. Please install with 'pip install windows-curses'.")
            sys.exit(1)
    else:
        raise ImportError("Failed to import the curses module.")

def draw_bar(stdscr, y, x, max_width, percentage, label):
    max_label_width = max_width - 20  # reserve some space for the bar itself
    label = label[:max_label_width]  # ensure label does not exceed the space
    bar_length = max_width - len(label) - 10 
    filled_length = int(bar_length * percentage / 100)
    bar_graph = f"{label} [{'#' * filled_length}{'.' * (bar_length - filled_length)}]"
    stdscr.addstr(y, x, bar_graph)

def draw_process_list(stdscr, start_y, start_x, processes, title, max_x):
    stdscr.addstr(start_y, start_x, title[:max_x])  # ensure the title fits within the screen width
    for i, proc in enumerate(processes):
        try:
            cpu_percent = 0.0 if proc.info['cpu_percent'] is None else proc.info['cpu_percent']
            memory_percent = 0.0 if proc.info['memory_percent'] is None else proc.info['memory_percent']
            proc_info = f"{proc.pid:>5} {proc.info['name'][:15]:<15} {cpu_percent:>5.1f}% {memory_percent:>5.1f}%"
            stdscr.addstr(start_y + i + 1, start_x, proc_info[:max_x])
        except (psutil.NoSuchProcess, psutil.AccessDenied, curses.error) as e:
            print("Error displaying process:", e)


def get_top_processes_by_cpu():
    processes = psutil.process_iter(['name', 'cpu_percent', 'memory_percent'])
    valid_processes = []
    for p in processes:
        try:
            p.info['cpu_percent'] = 0.0 if p.info['cpu_percent'] is None else p.info['cpu_percent']
            p.info['memory_percent'] = 0.0 if p.info['memory_percent'] is None else p.info['memory_percent']
            valid_processes.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(valid_processes, key=lambda p: p.info['cpu_percent'], reverse=True)[:20]

def get_top_processes_by_memory():
    processes = psutil.process_iter(['name', 'cpu_percent', 'memory_percent'])
    valid_processes = []
    for p in processes:
        try:
            p.info['memory_percent'] = 0.0 if p.info['memory_percent'] is None else p.info['memory_percent']
            valid_processes.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(valid_processes, key=lambda p: p.info['memory_percent'], reverse=True)[:20]


def main(stdscr):
    curses.curs_set(0)  # hide the cursor
    curses.noecho()
    stdscr.nodelay(True)  # do not wait for input when calling getch
    
    try:
        while True:
            stdscr.erase()
            max_y, max_x = stdscr.getmaxyx()  # get the size of the window

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            mem_amount = memory.used
            mem_percent = memory.percent

            display_text = [
                f"CPU Usage: {cpu_percent}%",
                f"Memory Usage: {round(mem_amount / (1024 ** 3), 2)}GB ({mem_percent}%) of {round(memory.total / (1024 ** 3), 2)}GB",
            ]

            draw_bar(stdscr, 1, 0, max_x, cpu_percent, display_text[0])
            draw_bar(stdscr, 3, 0, max_x, mem_percent, display_text[1])

            top_cpu = get_top_processes_by_cpu()
            top_memory = get_top_processes_by_memory()
            half_width = max_x // 2
            draw_process_list(stdscr, 5, 0, top_cpu, "Top CPU Processes", max_x // 2)
            draw_process_list(stdscr, 5, half_width, top_memory, "Top Memory Processes", max_x // 2)

            stdscr.refresh()
            time.sleep(1)  # update interval

            # check for the 'q' key to quit
            k = stdscr.getch()
            if k == ord('q'):
                break
    except KeyboardInterrupt:
        # handle ctrl + c gracefully
        pass
    finally:
        # cleanup
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

curses.wrapper(main)
