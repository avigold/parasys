import sys
import psutil
from collections import deque

try:
    import curses
except ImportError:
    if sys.platform.startswith('win'):
        try:
            import windows_curses as curses
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

def draw_line_graph(stdscr, y, x, data, label, width):
    stdscr.addstr(y, x, label)
    max_data = max(data) if data else 1
    graph_height = 10
    data_points = list(data)[-width:]
    for i, value in enumerate(data_points):
        bar_height = int((value / max_data) * graph_height)
        for j in range(graph_height):
            char = '#' if j < bar_height else ' '
            stdscr.addstr(y + graph_height - j, x + i + len(label) + 1, char)

def draw_process_list(stdscr, start_y, start_x, processes, title, max_x, max_y, display_type):
    stdscr.addstr(start_y, start_x, title[:max_x])

    if display_type == 'cpu':
        headers = "  PID Name               CPU%"
    elif display_type == 'memory':
        headers = "  PID Name               MEM%"

    stdscr.addstr(start_y + 1, start_x, headers[:max_x])
    max_processes = max_y - start_y - 3

    for i, proc in enumerate(processes[:max_processes]):
        try:
            if display_type == 'cpu':
                num_cores = psutil.cpu_count
                cpu_percent = proc['cpu_percent']
                proc_info = f"{proc['pid']:>5} {proc['name'][:15]:<15} {cpu_percent / num_cores():>6.1f}%"
            elif display_type == 'memory':
                memory_percent = proc['memory_percent']
                proc_info = f"{proc['pid']:>5} {proc['name'][:15]:<15} {memory_percent:>6.1f}%"
            stdscr.addstr(start_y + i + 2, start_x, proc_info[:max_x])
        except curses.error:
            continue

def get_top_processes_by_cpu():
    processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent']))
    valid_processes = []
    for p in processes:
        try:
            cpu_percent = p.cpu_percent(interval=None)
            valid_processes.append({'pid': p.pid, 'name': p.info['name'], 'cpu_percent': cpu_percent})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(valid_processes, key=lambda p: p['cpu_percent'], reverse=True)[:20]

def get_top_processes_by_memory():
    processes = psutil.process_iter(['pid', 'name', 'memory_percent'])
    valid_processes = []
    for p in processes:
        try:
            memory_percent = p.memory_percent()
            valid_processes.append({'pid': p.pid, 'name': p.info['name'], 'memory_percent': memory_percent})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(valid_processes, key=lambda p: p['memory_percent'], reverse=True)[:20]

def main(stdscr):
    curses.curs_set(0) # hide cursor
    curses.noecho()
    stdscr.nodelay(True)

    cpu_data = deque(maxlen=50)
    memory_data = deque(maxlen=50)
    
    try:
        while True:
            stdscr.erase()
            max_y, max_x = stdscr.getmaxyx()

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            mem_amount = memory.used
            mem_percent = memory.percent

            cpu_data.append(cpu_percent)
            memory_data.append(mem_percent)

            draw_line_graph(stdscr, 1, 0, list(cpu_data), "CPU Usage Over Time: ", max_x - 1)
            draw_line_graph(stdscr, 15, 0, list(memory_data), "Memory Usage Over Time: ", max_x - 1)

            draw_bar(stdscr, 13, 0, max_x, cpu_percent, f"Current CPU Usage: {cpu_percent}%")
            draw_bar(stdscr, 27, 0, max_x, mem_percent, f"CurrentMemory Usage: {round(mem_amount / (1024 ** 3), 2)}GB ({mem_percent}%) of {round(memory.total / (1024 ** 3), 2)}GB")

            top_cpu = get_top_processes_by_cpu()
            top_memory = get_top_processes_by_memory()
            half_width = max_x // 2
            draw_process_list(stdscr, 30, 0, top_cpu, "Top CPU Processes", half_width, max_y, 'cpu')
            draw_process_list(stdscr, 30, half_width, top_memory, "Top Memory Processes", half_width, max_y, 'memory')

            stdscr.refresh()

            # pressing q can quit
            k = stdscr.getch()
            if k == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

curses.wrapper(main)
