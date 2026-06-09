import os
import re
import time
import tempfile
import subprocess
import threading
from pathlib import Path

import psutil


LANGUAGE_INFO = {
    'python':  {'ext': '.py', 'name': 'Python',  'run_cmd': ['python3']},
    'c':       {'ext': '.c',  'name': 'C',       'compile_cmd': ['gcc', '-O0', '-o'], 'run_cmd': []},
    'cpp':     {'ext': '.cpp','name': 'C++',     'compile_cmd': ['g++', '-O0', '-o'], 'run_cmd': []},
    'java':    {'ext': '.java','name': 'Java',   'compile_cmd': ['javac'], 'run_cmd': ['java']},
    'csharp':  {'ext': '.cs', 'name': 'C#',      'compile_cmd': ['csc', '-out:'], 'run_cmd': ['mono']},
    'fortran': {'ext': '.f90','name': 'Fortran', 'compile_cmd': ['gfortran', '-O0', '-o'], 'run_cmd': []},
}


DETECT_PATTERNS = {
    'python': [r'import\s+\w+', r'def\s+\w+\s*\(', r'class\s+\w+\s*:', r'print\s*\('],
    'java': [r'public\s+(class|static)', r'class\s+\w+\s*\{', r'System\.out\.', r'import\s+java\.'],
    'c': [r'#include\s*<stdio', r'int\s+main\s*\(', r'#include\s*<stdlib'],
    'cpp': [r'#include\s*<iostream', r'std::', r'#include\s*<vector', r'#include\s*<string'],
    'csharp': [r'using\s+System', r'namespace\s+\w+', r'class\s+\w+\s*\{'],
    'fortran': [r'program\s+\w+', r'end\s+program', r'integer\s*::', r'real\s*::'],
}

GUI_INDICATORS = {
    'python': ['tkinter', 'PyQt', 'PySide', 'wx', 'gtk', 'PyGTK',
               'PyGame', 'sdl2', 'kivy', 'dearpygui', 'PySimpleGUI',
               'matplotlib.pyplot', 'matplotlib.figure'],
    'java': ['javax.swing', 'java.awt', 'javafx'],
    'c': ['gtk', 'SDL', 'glut', 'glfw', 'wx', 'raylib', 'ncurses'],
    'cpp': ['gtk', 'SDL', 'glut', 'glfw', 'wx', 'raylib', 'Qt',
            'FLTK', 'ncurses', 'imgui'],
    'csharp': ['System.Windows', 'System.Drawing',
               'System.Windows.Forms', 'PresentationFramework',
               'System.Windows.Controls', 'Avalonia'],
    'fortran': ['dislin', 'plot'],
}

EMPTY_RESULT = {
    'success': False, 'output': '', 'error': '',
    'language': '', 'needs_gui': False,
    'cpu':  {'percent': 0, 'graph': {'x': [], 'y': []}, 'human': '0%', 'max': 0, 'avg': 0},
    'gpu':  {'percent': 0, 'graph': {'x': [], 'y': []}, 'human': 'N/A', 'max': 0, 'avg': 0, 'available': False},
    'ram':  {'percent': 0, 'graph': {'x': [], 'y': []}, 'human': '0 B', 'max': 0, 'avg': 0},
    'ssd':  {'percent': 0, 'graph': {'x': [], 'y_read': [], 'y_write': []}, 'human': '0 B read, 0 B written',
             'read_total': 0, 'write_total': 0},
    'time': {'value': 0, 'human': '0.00s', 'percent': 100},
}


def detect_language(code, hint=None):
    if hint and hint != 'auto':
        return hint.lower()
    scores = {}
    for lang, patterns in DETECT_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, code, re.IGNORECASE))
        if score:
            scores[lang] = score
    return max(scores, key=scores.get) if scores else 'python'


def detect_needs_gui(code, language):
    code_lower = code.lower()
    for indicator in GUI_INDICATORS.get(language, []):
        if indicator.lower() in code_lower:
            return True
    extra = {
        'java': [r'extends\s+(JFrame|JPanel|Application)', r'implements\s+ActionListener'],
        'cpp':  [r'QApplication', r'QWidget'],
        'csharp': [r':\s*Form', r':\s*Window', r':\s*Page'],
        'python': [r'\.mainloop\(\)', r'\.run\(\)', r'\.exec\(\)'],
    }
    for lang, pats in extra.items():
        if lang == language:
            for p in pats:
                if re.search(p, code):
                    return True
    return False


def _fmt_bytes(n):
    n = max(0, n)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024:
            return f'{n:.2f} {unit}'
        n /= 1024
    return f'{n:.2f} PB'


class ResourceMonitor:
    def __init__(self, process):
        self.process = process
        self.running = True
        self.lock = threading.Lock()
        self.data = {
            'timestamps': [], 'cpu_percent': [], 'memory_rss': [],
            'disk_read': [], 'disk_write': [], 'gpu_percent': [],
        }
        self._thread = None
        self._system_mem = psutil.virtual_memory().total
        self._gpu_available = self._check_gpu()

        self._cpu_start = None
        self._io_start = None
        if process:
            try:
                self._cpu_start = process.cpu_times()
                self._io_start = process.io_counters()
                process.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.process = None

    def _check_gpu(self):
        try:
            r = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True, text=True, timeout=3
            )
            return r.returncode == 0 and r.stdout.strip()
        except Exception:
            return False

    def _query_gpu(self):
        if not self._gpu_available:
            return None
        try:
            r = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=2
            )
            vals = r.stdout.strip().split('\n')
            if vals and vals[0]:
                return float(vals[0])
        except Exception:
            pass
        return 0.0

    def _monitor_loop(self):
        while self.running:
            if not self.process:
                time.sleep(0.02)
                continue
            try:
                ts = time.time()
                cpu = self.process.cpu_percent()
                mem = self.process.memory_info().rss
                io = self.process.io_counters()
                gpu = self._query_gpu()
                with self.lock:
                    self.data['timestamps'].append(ts)
                    self.data['cpu_percent'].append(cpu)
                    self.data['memory_rss'].append(mem)
                    self.data['disk_read'].append(io.read_bytes if io else 0)
                    self.data['disk_write'].append(io.write_bytes if io else 0)
                    self.data['gpu_percent'].append(gpu)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                if self.running:
                    with self.lock:
                        self.data['timestamps'].append(time.time())
                        for k in ('cpu_percent', 'memory_rss', 'disk_read', 'disk_write'):
                            self.data[k].append(0)
                        self.data['gpu_percent'].append(None)
            except Exception:
                pass
            time.sleep(0.02)

    def start(self):
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)

    def get_results(self, elapsed_time):
        with self.lock:
            timestamps = list(self.data['timestamps'])
            cpu_percent_samples = list(self.data['cpu_percent'])
            mem_samples = list(self.data['memory_rss'])
            gpu_samples = list(self.data['gpu_percent'])
            disk_read_samples = list(self.data['disk_read'])
            disk_write_samples = list(self.data['disk_write'])

        try:
            cpu_times_end = self.process.cpu_times() if self.process else None
            io_end = self.process.io_counters() if self.process else None
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            cpu_times_end = None
            io_end = None

        # Accurate CPU from cumulative times
        if self._cpu_start and cpu_times_end:
            user_delta = cpu_times_end.user - self._cpu_start.user
            sys_delta = cpu_times_end.system - self._cpu_start.system
            total_cpu_time = user_delta + sys_delta
            cpu_percent_from_times = (total_cpu_time / elapsed_time) * 100 if elapsed_time > 0 else 0
        else:
            cpu_percent_from_times = 0

        # Use polled CPU if available and matching, else use time-based
        cpu_avg_from_polls = (sum(cpu_percent_samples) / len(cpu_percent_samples)
                              if cpu_percent_samples else 0)
        cpu_avg = max(cpu_percent_from_times, cpu_avg_from_polls)
        cpu_max = max(cpu_percent_samples) if cpu_percent_samples else cpu_avg

        # Memory
        mem_max = max(mem_samples) if mem_samples else 0
        mem_avg = sum(mem_samples) / len(mem_samples) if mem_samples else 0
        mem_percent = (mem_max / self._system_mem) * 100 if self._system_mem > 0 else 0

        # GPU
        valid_gpu = [g for g in gpu_samples if g is not None]
        if valid_gpu:
            gpu_avg = sum(valid_gpu) / len(valid_gpu)
            gpu_max = max(valid_gpu)
            gpu_y = valid_gpu
            gpu_human = f'{gpu_avg:.1f}% avg ({gpu_max:.1f}% peak)'
            gpu_avail = True
        else:
            gpu_avg = 0.0; gpu_max = 0.0
            gpu_y = []
            gpu_human = 'No NVIDIA GPU detected'
            gpu_avail = False

        # Disk I/O
        if self._io_start and io_end:
            read_total = max(0, io_end.read_bytes - self._io_start.read_bytes)
            write_total = max(0, io_end.write_bytes - self._io_start.write_bytes)
        elif len(disk_read_samples) > 1:
            read_total = max(0, disk_read_samples[-1] - disk_read_samples[0])
            write_total = max(0, disk_write_samples[-1] - disk_write_samples[0])
        else:
            read_total = write_total = 0

        disk_max = max(50 * 1024 * 1024, read_total + write_total)
        disk_percent = min((read_total + write_total) / disk_max * 100, 100)

        # Build time axis
        if timestamps:
            t0 = timestamps[0]
            time_axis = [t - t0 for t in timestamps]
        else:
            time_axis = [0.0, elapsed_time]
            cpu_percent_samples = [0, 0]
            mem_samples = [0, 0]
            disk_read_samples = [0, 0]
            disk_write_samples = [0, 0]

        return {
            'cpu': {
                'percent': cpu_avg,
                'graph': {'x': time_axis, 'y': cpu_percent_samples},
                'human': f'{cpu_avg:.1f}% avg ({cpu_max:.1f}% peak)',
                'max': cpu_max, 'avg': cpu_avg,
            },
            'gpu': {
                'percent': gpu_avg,
                'graph': {'x': time_axis, 'y': gpu_y},
                'human': gpu_human,
                'max': gpu_max, 'avg': gpu_avg,
                'available': gpu_avail,
            },
            'ram': {
                'percent': mem_percent,
                'graph': {'x': time_axis, 'y': [m / (1024 * 1024) for m in mem_samples]},
                'human': f'{_fmt_bytes(mem_max)} ({mem_percent:.1f}% of {_fmt_bytes(self._system_mem)})',
                'max': mem_max, 'avg': mem_avg,
            },
            'ssd': {
                'percent': disk_percent,
                'graph': {
                    'x': time_axis,
                    'y_read': [r - disk_read_samples[0] for r in disk_read_samples],
                    'y_write': [w - disk_write_samples[0] for w in disk_write_samples],
                },
                'human': f'{_fmt_bytes(read_total)} read, {_fmt_bytes(write_total)} written',
                'read_total': read_total, 'write_total': write_total,
            },
            'time': {
                'value': elapsed_time,
                'human': f'{elapsed_time:.3f}s',
                'percent': 100,
            },
        }


def _make_error(error, language, needs_gui):
    r = dict(EMPTY_RESULT)
    r.update(success=False, error=error, language=language, needs_gui=needs_gui)
    return r


def run_code(code, language='auto', timeout=30):
    language = detect_language(code, language)
    needs_gui = detect_needs_gui(code, language)
    info = LANGUAGE_INFO.get(language, LANGUAGE_INFO['python'])

    with tempfile.NamedTemporaryFile(mode='w', suffix=info['ext'], delete=False) as f:
        f.write(code)
        temp_path = f.name

    base = os.path.splitext(temp_path)[0]
    exe_path = base + ('.out' if os.name != 'nt' else '.exe')

    try:
        compile_cmd = info.get('compile_cmd')
        if compile_cmd:
            if language == 'java':
                cmd = list(compile_cmd) + [temp_path]
            elif language == 'csharp':
                cmd = list(compile_cmd) + [exe_path, temp_path]
            else:
                cmd = list(compile_cmd) + [exe_path, temp_path]
            comp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if comp.returncode != 0:
                return _make_error(comp.stderr or comp.stdout, language, needs_gui)

        if language == 'python':
            run_cmd = ['python3', temp_path]
        elif language == 'java':
            run_cmd = ['java', '-cp', os.path.dirname(temp_path),
                       os.path.splitext(os.path.basename(temp_path))[0]]
        elif language == 'csharp':
            run_cmd = ['mono', exe_path] if os.name != 'nt' else [exe_path]
        elif compile_cmd and os.path.exists(exe_path):
            run_cmd = [exe_path]
        else:
            rc = info.get('run_cmd', [temp_path])
            run_cmd = rc if rc else [temp_path]

        start = time.time()
        proc = subprocess.Popen(run_cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)

        monitor = ResourceMonitor(psutil.Process(proc.pid))
        monitor.start()

        try:
            out_b, err_b = proc.communicate(timeout=timeout)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill(); proc.communicate()
            out_b, err_b, rc = '', 'Execution timed out', -1

        elapsed = max(time.time() - start, 0.001)
        monitor.stop()
        results = monitor.get_results(elapsed)
        results.update(success=rc == 0, output=out_b, error=err_b,
                       language=language, needs_gui=needs_gui)
        return results

    except FileNotFoundError as e:
        return _make_error(f'Tool not found: {e.filename}. Install the compiler/interpreter.',
                           language, needs_gui)
    except Exception as e:
        return _make_error(str(e), language, needs_gui)
    finally:
        for p in [temp_path, exe_path]:
            try:
                if os.path.exists(p): os.unlink(p)
            except Exception:
                pass
        if language == 'java':
            try:
                for f in Path(temp_path).parent.glob(f'{Path(temp_path).stem}*.class'):
                    f.unlink()
            except Exception:
                pass
