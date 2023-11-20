import subprocess
import json
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

def parse_metric(value):
    if isinstance(value, (int, float)):
        return value
    # If value is a string, attempt to parse it as a float
    if isinstance(value, str):
        # Remove non-numeric characters like commas and units (e.g., "ms", "s")
        value = re.sub(r'[^\d.]+', '', value.replace(',', ''))
        try:
            return float(value)
        except ValueError:
            pass  
    return 0.0


def run_lighthouse(url, number_of_runs):
    accum_metrics = {
        'Performance Score': 0,
        'First Contentful Paint': 0,
        'Speed Index': 0,
        'Largest Contentful Paint': 0,
        'Time to Interactive': 0,
        'Total Blocking Time': 0,
        'Cumulative Layout Shift': 0,
    }
    successful_runs = 0 
    for _ in range(number_of_runs):
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url

            # Run the Lighthouse audit
            process = subprocess.run(['lighthouse', url, '--output=json', '--quiet', '--no-enable-error-reporting'],
                                     capture_output=True, text=True, timeout=300)

            if process.returncode != 0:
                print(f"Lighthouse failed for {url} with the message: {process.stderr.strip()}")
                return url, "Lighthouse failed to run"

            results = json.loads(process.stdout)

            accum_metrics['Performance Score'] += results['categories']['performance']['score'] * 100
            accum_metrics['First Contentful Paint'] += results['audits']['first-contentful-paint']['numericValue']
            accum_metrics['Speed Index'] += results['audits']['speed-index']['numericValue']
            accum_metrics['Largest Contentful Paint'] += results['audits']['largest-contentful-paint']['numericValue']
            accum_metrics['Time to Interactive'] += results['audits']['interactive']['numericValue']
            accum_metrics['Total Blocking Time'] += results['audits']['total-blocking-time']['numericValue']
            accum_metrics['Cumulative Layout Shift'] += results['audits']['cumulative-layout-shift']['numericValue']

            successful_runs += 1
        except subprocess.CalledProcessError as e:
            print(f"Error running Lighthouse for {url}: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decoding error for {url}: {e}")
        except subprocess.TimeoutExpired as e:
            print(f"Timeout running Lighthouse for {url}: {e}")

    averaged_metrics = {}
    if successful_runs > 0:
        for key in accum_metrics:
            average = accum_metrics[key] / successful_runs
            if key in ['First Contentful Paint', 'Speed Index', 'Largest Contentful Paint', 
                       'Time to Interactive', 'Total Blocking Time']:
                averaged_metrics[key] = round(average / 1000, 2)  # Convert from ms to s
            elif key == 'Cumulative Layout Shift':
                averaged_metrics[key] = round(average, 2)
            else:
                averaged_metrics[key] = round(average, 2)
    else:
        return url, "No successful Lighthouse runs"

    return url, averaged_metrics

def update_ui(result, result_labels):
    url, metrics = result
    if isinstance(metrics, dict):
        result_text = f"{url}\n" + "\n".join(f"{metric}: {value}" for metric, value in metrics.items())
    else:
        result_text = f"{url} - {metrics}" 
    result_labels[url]['text'] = result_text

def setup_ui():
    # Set up main window
    root = tk.Tk()
    root.title("Lighthouse Performance Tester")
    root.configure(bg='#07d9d9')  

    style = ttk.Style()
    style.theme_use('default')

    style.configure("Treeview",
                    background="#07d9d9",
                    foreground="white",
                    fieldbackground="#07d9d9")
    style.map('Treeview', background=[('selected', 'white')], foreground=[('selected', '#07d9d9')])

    style.configure("Treeview.Heading",
                    background="#07d9d9",
                    foreground="white")

    style.configure("TLabel", background="#07d9d9", foreground="white")

    style.configure("TButton", background="#07d9d9", foreground="white")

    style.configure("TEntry", fieldbackground="#07d9d9", foreground="white")

    style.configure("Vertical.TScrollbar", background="#07d9d9")

    input_frame = tk.Frame(root, bg='#07d9d9')
    input_frame.pack(pady=10)

    tk.Label(input_frame, text="Enter website URLs (one per line):", bg='#07d9d9', fg='white').grid(row=0, column=0, sticky='nw', padx=5)
    
    url_text = tk.Text(input_frame, height=10, width=50, bg='white', fg='black', insertbackground='black')
    url_text.grid(row=1, column=0, sticky='ew')

    scrollbar = ttk.Scrollbar(input_frame, command=url_text.yview)
    scrollbar.grid(row=1, column=1, sticky='ns')
    url_text['yscrollcommand'] = scrollbar.set

    tk.Label(input_frame, text="Number of tests per URL:", bg='#07d9d9', fg='white').grid(row=0, column=2, sticky='nw', padx=5)
    num_tests_entry = ttk.Entry(input_frame, style="TEntry")
    num_tests_entry.grid(row=1, column=2, sticky='nw', padx=5)
    num_tests_entry.insert(0, "1")  # Default value

    tk.Label(input_frame, text="Each test may take up to 1 minute.", bg='#07d9d9', fg='white').grid(row=2, column=0, columnspan=3, sticky='nw', padx=5)


    columns = ('url', 'performance', 'fcp', 'speed_index', 'lcp', 'tti', 'tbt', 'cls')
    results_tree = ttk.Treeview(root, columns=columns, show='headings')
    results_tree.pack(fill=tk.BOTH, expand=True)
    
    results_tree.heading('url', text="URL")
    results_tree.heading('performance', text="Performance")
    results_tree.heading('fcp', text="First Contentful Paint")
    results_tree.heading('speed_index', text="Speed Index")
    results_tree.heading('lcp', text="Largest Contentful Paint")
    results_tree.heading('tti', text="Time to Interactive")
    results_tree.heading('tbt', text="Total Blocking Time")
    results_tree.heading('cls', text="Cumulative Layout Shift")

    for col in columns:
        results_tree.column(col, width=100, anchor=tk.W)

    def treeview_sort_column(tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

    for col in columns:
        results_tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(results_tree, _col, False))

    def start_tests():
        for i in results_tree.get_children():
            results_tree.delete(i)

        urls = url_text.get("1.0", tk.END).splitlines()
        number_of_runs = int(num_tests_entry.get())

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(run_lighthouse, url, number_of_runs): url for url in urls if url}
            for future in as_completed(future_to_url):
                url, metrics = future.result()
                if isinstance(metrics, dict):
                    results_tree.insert('', tk.END, values=(
                        url,
                        f"{metrics['Performance Score']:.1f}",
                        metrics['First Contentful Paint'],
                        metrics['Speed Index'],
                        metrics['Largest Contentful Paint'],
                        metrics['Time to Interactive'],
                        metrics['Total Blocking Time'],
                        metrics['Cumulative Layout Shift'],
                    ))
                else:
                    results_tree.insert('', tk.END, values=(url, metrics))

    start_button = ttk.Button(root, text="Start Performance Test", command=start_tests)
    start_button.pack(pady=20)

    root.mainloop()

setup_ui()