import csv
import math
import os
import matplotlib.pyplot as plt

from params import K_VALUES, R_VALUES, RESULTS_FOLDER


def read_file(filename):
    path = os.path.join(RESULTS_FOLDER, filename)
    rows = []
    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(row)
    return rows


def to_number(value):
    if value == "":
        return ""
    if value == "inf":
        return math.inf
    return float(value)


def make_key(row):
    return int(row["K"]), float(row["r"]), row["node"]


def make_dictionary(rows):
    data = {}
    for row in rows:
        key = make_key(row)
        data[key] = {
            "U": to_number(row["U"]),
            "X": to_number(row["X_jobs_per_s"]),
            "J": to_number(row["J"]),
            "T_ms": to_number(row["T_ms"])
        }
    return data


def relative_error(analytical, simulation):
    #Odstupanje se ne računa za prazne, beskonačne i nulte vrijednosti
    if analytical == "":
        return ""
    if math.isinf(analytical):
        return ""
    if analytical == 0:
        return ""
    error = abs(simulation - analytical)
    return error / abs(analytical) * 100


def write_deviations(analytical, simulation, average):
    path = os.path.join(RESULTS_FOLDER, "relativna_odstupanja.csv")
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "K",
            "r",
            "node",
            "parameter",
            "analytical",
            "simulation",
            "error_simulation_percent",
            "simulation_average",
            "error_average_percent"
        ])
        parameters = ["U", "X", "J", "T_ms"]
        for key in analytical:
            k = key[0]
            r = key[1]
            node = key[2]
            for parameter in parameters:
                analytical_value = analytical[key][parameter]
                simulation_value = simulation[key][parameter]
                average_value = average[key][parameter]
                error_simulation = relative_error(
                    analytical_value,
                    simulation_value
                )
                error_average = relative_error(
                    analytical_value,
                    average_value
                )
                if error_simulation != "":
                    error_simulation = round(error_simulation, 6)
                if error_average != "":
                    error_average = round(error_average, 6)
                writer.writerow([
                    k,
                    r,
                    node,
                    parameter,
                    analytical_value,
                    simulation_value,
                    error_simulation,
                    average_value,
                    error_average
                ])


def write_error_summary(analytical, simulation, average):
    path = os.path.join(RESULTS_FOLDER, "sazetak_odstupanja.csv")
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "K",
            "r",
            "average_error_single_percent",
            "average_error_100_runs_percent"
        ])
        parameters = ["U", "X", "J", "T_ms"]
        for k in K_VALUES:
            for r in R_VALUES:
                single_errors = []
                average_errors = []
                for key in analytical:
                    if key[0] != k:
                        continue
                    if abs(key[1] - r) > 0.000001:
                        continue
                    for parameter in parameters:
                        analytical_value = analytical[key][parameter]
                        simulation_value = simulation[key][parameter]
                        average_value = average[key][parameter]
                        error_single = relative_error(
                            analytical_value,
                            simulation_value
                        )
                        error_average = relative_error(
                            analytical_value,
                            average_value
                        )
                        if error_single != "":
                            single_errors.append(error_single)
                        if error_average != "":
                            average_errors.append(error_average)
                if len(single_errors) > 0:
                    single_result = sum(single_errors) / len(single_errors)
                else:
                    single_result = ""
                if len(average_errors) > 0:
                    average_result = sum(average_errors) / len(average_errors)
                else:
                    average_result = ""
                if single_result != "":
                    single_result = round(single_result, 6)
                if average_result != "":
                    average_result = round(average_result, 6)
                writer.writerow([
                    k,
                    r,
                    single_result,
                    average_result
                ])


def write_critical_resources(rows):
    path = os.path.join(RESULTS_FOLDER, "kriticni_resursi.csv")
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "K",
            "r",
            "critical_resources"
        ])
        for k in K_VALUES:
            for r in R_VALUES:
                critical = []
                for row in rows:
                    same_k = int(row["K"]) == k
                    same_r = abs(float(row["r"]) - r) < 0.000001
                    is_critical = row["critical"].lower() == "true"
                    is_resource = row["node"] != "SYSTEM"
                    if same_k and same_r and is_critical and is_resource:
                        critical.append(row["node"])
                writer.writerow([
                    k,
                    r,
                    ", ".join(critical)
                ])


def find_row(rows, k, r, node):
    for row in rows:
        same_k = int(row["K"]) == k
        same_r = abs(float(row["r"]) - r) < 0.000001
        same_node = row["node"] == node
        if same_k and same_r and same_node:
            return row
    return None


def draw_utilization_graphs(rows):
    #Za grafik se uzimaju CPU, jedan sistemski i jedan korisnički disk
    for r in R_VALUES:
        cpu_values = []
        sd_values = []
        ud_values = []
        for k in K_VALUES:
            cpu_row = find_row(rows, k, r, "CPU")
            sd_row = find_row(rows, k, r, "SD2")
            ud_row = find_row(rows, k, r, "UD1")
            cpu_values.append(float(cpu_row["U"]))
            sd_values.append(float(sd_row["U"]))
            ud_values.append(float(ud_row["U"]))
        plt.figure(figsize=(7, 5))
        plt.plot(K_VALUES, cpu_values, marker="o", label="CPU")
        plt.plot(K_VALUES, sd_values, marker="s", label="SD2")
        plt.plot(K_VALUES, ud_values, marker="^", label="UD1")
        plt.xlabel("K")
        plt.ylabel("Iskoriscenje")
        plt.title("Iskoriscenje resursa za r = " + str(r))
        plt.xticks(K_VALUES)
        plt.grid()
        plt.legend()
        plt.tight_layout()
        filename = "iskoriscenje_r_" + str(r) + ".png"
        path = os.path.join(RESULTS_FOLDER, filename)
        plt.savefig(path)
        plt.close()


def draw_resource_time_graphs(rows):
    nodes = ["CPU", "SD2", "UD1"]
    markers = {
        "CPU": "o",
        "SD2": "s",
        "UD1": "^"
    }
    offsets = {
        "CPU": -0.08,
        "SD2": 0.0,
        "UD1": 0.08
    }
    for r in R_VALUES:
        values = {}
        finite_values = []
        for node in nodes:
            node_values = []
            for k in K_VALUES:
                row = find_row(rows, k, r, node)
                value = to_number(row["T_ms"])
                node_values.append(value)
                if not math.isinf(value):
                    finite_values.append(value)
            values[node] = node_values
        if len(finite_values) > 0:
            maximum = max(finite_values)
        else:
            maximum = 1
        infinity_height = maximum * 1.15
        plt.figure(figsize=(7, 5))
        for node in nodes:
            graph_values = []
            for value in values[node]:
                if math.isinf(value):
                    graph_values.append(None)
                else:
                    graph_values.append(value)
            plt.plot(
                K_VALUES,
                graph_values,
                marker=markers[node],
                label=node
            )
            #Beskonačne vrijednosti se označavaju znakom beskonačnosti
            for i in range(len(K_VALUES)):
                if math.isinf(values[node][i]):
                    x = K_VALUES[i] + offsets[node]
                    plt.text(
                        x,
                        infinity_height,
                        "∞",
                        ha="center",
                        va="bottom",
                        fontsize=14
                    )
        plt.xlabel("K")
        plt.ylabel("Vrijeme odziva [ms]")
        plt.title("Vrijeme odziva resursa za r = " + str(r))
        plt.xticks(K_VALUES)
        plt.ylim(bottom=0, top=infinity_height * 1.15)
        plt.grid()
        plt.legend()
        if r == 1.0:
            plt.text(
                0.02,
                0.95,
                "∞ oznacava kritican resurs",
                transform=plt.gca().transAxes,
                va="top"
            )
        plt.tight_layout()
        filename = "vrijeme_resursa_r_" + str(r) + ".png"
        path = os.path.join(RESULTS_FOLDER, filename)
        plt.savefig(path)
        plt.close()


def draw_system_time_graphs(rows):
    for r in R_VALUES:
        values = []
        infinite = False
        for k in K_VALUES:
            row = find_row(rows, k, r, "SYSTEM")
            value = to_number(row["T_ms"])
            if math.isinf(value):
                infinite = True
            values.append(value)
        plt.figure(figsize=(7, 5))
        if infinite:
            #Na granici stabilnosti vrijeme odziva je beskonačno
            plt.text(
                0.5,
                0.5,
                "Za r = 1 vrijeme odziva sistema je beskonacno.",
                ha="center",
                va="center",
                transform=plt.gca().transAxes
            )
            plt.xticks([])
            plt.yticks([])
        else:
            plt.plot(K_VALUES, values, marker="o")
            plt.xlabel("K")
            plt.ylabel("Vrijeme odziva sistema [ms]")
            plt.xticks(K_VALUES)
            plt.grid()
        plt.title("Vrijeme odziva sistema za r = " + str(r))
        plt.tight_layout()
        filename = "vrijeme_sistema_r_" + str(r) + ".png"
        path = os.path.join(RESULTS_FOLDER, filename)
        plt.savefig(path)
        plt.close()


def run_comparison():
    analytical_rows = read_file("rezultati_analiticki.csv")
    simulation_rows = read_file("rezultati_simulacija.csv")
    average_rows = read_file("rezultati_simulacija_usrednjeno.csv")
    analytical = make_dictionary(analytical_rows)
    simulation = make_dictionary(simulation_rows)
    average = make_dictionary(average_rows)
    write_deviations(analytical, simulation, average)
    write_error_summary(analytical, simulation, average)
    write_critical_resources(analytical_rows)
    draw_utilization_graphs(analytical_rows)
    draw_resource_time_graphs(analytical_rows)
    draw_system_time_graphs(analytical_rows)
    print("Poredjenje i grafikoni su napravljeni.")