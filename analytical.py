import csv
import math
import os
import matplotlib.pyplot as plt
import numpy as np

from params import (
    K_VALUES, R_VALUES, CPU_TIME, SYSTEM_DISK_1_TIME,
    SYSTEM_DISK_2_TIME, SYSTEM_DISK_3_TIME, USER_DISK_TIME,
    CPU_TO_CPU, CPU_TO_SYSTEM_DISK_1, CPU_TO_SYSTEM_DISK_2,
    CPU_TO_SYSTEM_DISK_3, CPU_TO_USER_DISKS, SYSTEM_DISK_TO_CPU,
    SYSTEM_DISK_TO_SAME_DISK, SYSTEM_DISK_TO_USER_DISKS,
    RESULTS_FOLDER, EPS
)


def get_names(k):
    names = ["CPU", "SD1", "SD2", "SD3"]
    for i in range(1, k + 1):
        names.append("UD" + str(i))
    return names


def get_times(k):
    times = [
        CPU_TIME,
        SYSTEM_DISK_1_TIME,
        SYSTEM_DISK_2_TIME,
        SYSTEM_DISK_3_TIME
    ]
    for i in range(k):
        times.append(USER_DISK_TIME)
    return np.array(times)


def make_matrix(k):
    number_of_resources = 4 + k
    p = np.zeros((number_of_resources, number_of_resources))

    #Prelazi poslije procesora
    p[0][0] = CPU_TO_CPU
    p[0][1] = CPU_TO_SYSTEM_DISK_1
    p[0][2] = CPU_TO_SYSTEM_DISK_2
    p[0][3] = CPU_TO_SYSTEM_DISK_3
    for i in range(4, number_of_resources):
        p[0][i] = CPU_TO_USER_DISKS / k

    #Prelazi poslije sistemskih diskova
    for disk in range(1, 4):
        p[disk][0] = SYSTEM_DISK_TO_CPU
        p[disk][disk] = SYSTEM_DISK_TO_SAME_DISK
        for i in range(4, number_of_resources):
            p[disk][i] = SYSTEM_DISK_TO_USER_DISKS / k

    #Poslije korisničkog diska posao izlazi
    return p


def calculate_basic_data(k):
    names = get_names(k)
    times = get_times(k)
    p = make_matrix(k)
    number_of_resources = len(names)

    #Spoljašnji poslovi dolaze samo na procesor
    external_flow = np.zeros(number_of_resources)
    external_flow[0] = 1.0

    #Rješavanje sistema (I - P^T) * V = e
    matrix = np.eye(number_of_resources) - p.T
    visit_ratios = np.linalg.solve(matrix, external_flow)

    #Servisni zahtjevi resursa
    demands = visit_ratios * times
    maximum_demand = max(demands)
    alpha_max = 1.0 / maximum_demand

    #Traženje kritičnih resursa
    critical_resources = []
    for i in range(number_of_resources):
        if abs(demands[i] - maximum_demand) < EPS:
            critical_resources.append(names[i])

    return names, times, visit_ratios, alpha_max, critical_resources


def clean_number(number):
    if isinstance(number, float):
        if math.isinf(number):
            return "inf"
        return round(number, 10)
    return number


def run_analytical():
    os.makedirs(RESULTS_FOLDER, exist_ok=True)

    #Putanje izlaznih fajlova
    flow_path = os.path.join(RESULTS_FOLDER, "protoci_analiticki.csv")
    limit_path = os.path.join(RESULTS_FOLDER, "granice_analiticki.csv")
    result_path = os.path.join(RESULTS_FOLDER, "rezultati_analiticki.csv")

    flow_file = open(flow_path, "w", newline="", encoding="utf-8")
    limit_file = open(limit_path, "w", newline="", encoding="utf-8")
    result_file = open(result_path, "w", newline="", encoding="utf-8")

    flow_writer = csv.writer(flow_file)
    limit_writer = csv.writer(limit_file)
    result_writer = csv.writer(result_file)

    #Zaglavlja csv fajlova
    flow_writer.writerow(["K", "node", "lambda_over_alpha"])
    limit_writer.writerow(["K", "alpha_max", "critical_resources"])
    result_writer.writerow([
        "K", "r", "alpha_jobs_per_s", "node", "U",
        "X_jobs_per_s", "J", "T_ms", "critical"
    ])

    #Podaci za grafik
    graph_k = []
    graph_alpha = []

    print()
    print("ANALITIČKI REZULTATI")
    print("-" * 60)

    for k in K_VALUES:
        names, times, visit_ratios, alpha_max, critical_resources = calculate_basic_data(k)
        graph_k.append(k)
        graph_alpha.append(alpha_max)

        limit_writer.writerow([
            k,
            clean_number(alpha_max),
            ", ".join(critical_resources)
        ])

        for i in range(len(names)):
            flow_writer.writerow([
                k,
                names[i],
                clean_number(visit_ratios[i])
            ])

        print(
            "K =", k,
            "| alpha_max =", round(alpha_max, 2),
            "| kritični resursi =", ", ".join(critical_resources)
        )

        for r in R_VALUES:
            alpha = r * alpha_max

            #Protoci i iskorišćenja resursa
            flows = alpha * visit_ratios
            utilizations = flows * times
            total_jobs = 0.0
            infinite_system = False

            for i in range(len(names)):
                utilization = utilizations[i]
                flow = flows[i]

                #Parametri jednog resursa
                if utilization >= 1.0 - EPS:
                    average_jobs = math.inf
                    response_time_ms = math.inf
                    infinite_system = True
                else:
                    average_jobs = utilization / (1.0 - utilization)
                    response_time_seconds = times[i] / (1.0 - utilization)
                    response_time_ms = response_time_seconds * 1000
                    total_jobs += average_jobs

                result_writer.writerow([
                    k,
                    r,
                    clean_number(alpha),
                    names[i],
                    clean_number(utilization),
                    clean_number(flow),
                    clean_number(average_jobs),
                    clean_number(response_time_ms),
                    names[i] in critical_resources
                ])

            #Parametri cijelog sistema
            if infinite_system:
                system_jobs = math.inf
                system_time_ms = math.inf
            else:
                system_jobs = total_jobs
                system_time_seconds = system_jobs / alpha
                system_time_ms = system_time_seconds * 1000

            result_writer.writerow([
                k,
                r,
                clean_number(alpha),
                "SYSTEM",
                "",
                clean_number(alpha),
                clean_number(system_jobs),
                clean_number(system_time_ms),
                infinite_system
            ])

    flow_file.close()
    limit_file.close()
    result_file.close()

    #Grafik maksimalnog ulaznog toka
    plt.figure(figsize=(7, 5))
    plt.plot(graph_k, graph_alpha, marker="o")
    plt.xticks(graph_k)
    plt.xlabel("K")
    plt.ylabel("alpha_max [poslova/s]")
    plt.title("Zavisnost maksimalnog ulaznog toka od K")
    plt.grid()
    plt.tight_layout()

    graph_path = os.path.join(RESULTS_FOLDER, "alpha_max.png")
    plt.savefig(graph_path)
    plt.close()

    print()
    print("Analitički fajlovi su napravljeni")