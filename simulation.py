import csv
import heapq
import os
import random
from collections import deque
from concurrent.futures import ProcessPoolExecutor

from analytical import calculate_basic_data
from params import (
    K_VALUES, R_VALUES, CPU_TIME, SYSTEM_DISK_1_TIME,
    SYSTEM_DISK_2_TIME, SYSTEM_DISK_3_TIME, USER_DISK_TIME,
    CPU_TO_CPU, CPU_TO_SYSTEM_DISK_1, CPU_TO_SYSTEM_DISK_2,
    CPU_TO_SYSTEM_DISK_3, SYSTEM_DISK_TO_CPU,
    SYSTEM_DISK_TO_SAME_DISK, NUMBER_OF_SIMULATIONS,
    RESULTS_FOLDER
)


def get_simulation_names(k):
    names = ["CPU", "SD1", "SD2", "SD3"]
    for i in range(1, k + 1):
        names.append("UD" + str(i))
    return names


def get_simulation_times(k):
    times = [
        CPU_TIME,
        SYSTEM_DISK_1_TIME,
        SYSTEM_DISK_2_TIME,
        SYSTEM_DISK_3_TIME
    ]
    for i in range(k):
        times.append(USER_DISK_TIME)
    return times


def choose_next_resource(resource, k):
    number = random.random()
    #Rutiranje poslije procesora
    if resource == 0:
        if number < CPU_TO_CPU:
            return 0
        if number < CPU_TO_CPU + CPU_TO_SYSTEM_DISK_1:
            return 1
        if number < CPU_TO_CPU + CPU_TO_SYSTEM_DISK_1 + CPU_TO_SYSTEM_DISK_2:
            return 2
        if number < CPU_TO_CPU + CPU_TO_SYSTEM_DISK_1 + CPU_TO_SYSTEM_DISK_2 + CPU_TO_SYSTEM_DISK_3:
            return 3
        return random.randrange(4, 4 + k)
    #Rutiranje poslije sistemskog diska
    if 1 <= resource <= 3:
        if number < SYSTEM_DISK_TO_CPU:
            return 0
        if number < SYSTEM_DISK_TO_CPU + SYSTEM_DISK_TO_SAME_DISK:
            return resource
        return random.randrange(4, 4 + k)
    #Poslije korisničkog diska posao izlazi
    return -1


def simulate(k, r, alpha, seed, simulation_time):
    random.seed(seed)
    names = get_simulation_names(k)
    times = get_simulation_times(k)
    number_of_resources = len(names)
    #Red čekanja za svaki resurs
    queues = []
    for i in range(number_of_resources):
        queues.append(deque())
    #Podaci potrebni za statistike
    busy = [False] * number_of_resources
    busy_start = [0.0] * number_of_resources
    total_busy_time = [0.0] * number_of_resources
    number_of_jobs = [0] * number_of_resources
    job_area = [0.0] * number_of_resources
    last_change = [0.0] * number_of_resources
    finished_jobs = [0] * number_of_resources
    response_sum = [0.0] * number_of_resources
    system_finished = 0
    system_response_sum = 0.0
    #Red budućih događaja
    events = []
    event_id = 0

    def add_event(event_time, event_type, resource, system_arrival, resource_arrival):
        nonlocal event_id
        event = (
            event_time,
            event_id,
            event_type,
            resource,
            system_arrival,
            resource_arrival
        )
        heapq.heappush(events, event)
        event_id += 1

    def update_area(resource, current_time):
        time_difference = current_time - last_change[resource]
        job_area[resource] += number_of_jobs[resource] * time_difference
        last_change[resource] = current_time

    def start_service(resource, system_arrival, resource_arrival, current_time):
        busy[resource] = True
        busy_start[resource] = current_time
        #Trajanje obrade ima eksponencijalnu raspodjelu
        service_time = random.expovariate(1.0 / times[resource])
        finish_time = current_time + service_time
        add_event(finish_time, "finish", resource, system_arrival, resource_arrival)

    def add_job(resource, system_arrival, current_time):
        update_area(resource, current_time)
        number_of_jobs[resource] += 1
        if busy[resource]:
            #Ako je resurs zauzet posao čeka
            queues[resource].append((system_arrival, current_time))
        else:
            start_service(resource, system_arrival, current_time, current_time)

    #Prvi spoljašnji dolazak na procesor
    first_arrival = random.expovariate(alpha)
    add_event(first_arrival, "arrival", -1, 0.0, 0.0)
    while len(events) > 0:
        event = heapq.heappop(events)
        current_time = event[0]
        event_type = event[2]
        resource = event[3]
        system_arrival = event[4]
        resource_arrival = event[5]
        if current_time > simulation_time:
            break
        if event_type == "arrival":
            #Novi posao ulazi na procesor
            add_job(0, current_time, current_time)
            next_arrival = current_time + random.expovariate(alpha)
            if next_arrival <= simulation_time:
                add_event(next_arrival, "arrival", -1, 0.0, 0.0)
        else:
            #Završena obrada na resursu
            update_area(resource, current_time)
            number_of_jobs[resource] -= 1
            total_busy_time[resource] += current_time - busy_start[resource]
            finished_jobs[resource] += 1
            response_sum[resource] += current_time - resource_arrival
            if len(queues[resource]) > 0:
                #Uzima se prvi posao iz reda
                next_job = queues[resource].popleft()
                start_service(resource, next_job[0], next_job[1], current_time)
            else:
                busy[resource] = False
            next_resource = choose_next_resource(resource, k)
            if next_resource == -1:
                #Posao napušta sistem
                system_finished += 1
                system_response_sum += current_time - system_arrival
            else:
                add_job(next_resource, system_arrival, current_time)
    rows = []
    system_average_jobs = 0.0
    #Računanje rezultata za svaki resurs
    for i in range(number_of_resources):
        job_area[i] += number_of_jobs[i] * (simulation_time - last_change[i])
        if busy[i]:
            total_busy_time[i] += simulation_time - busy_start[i]
        utilization = total_busy_time[i] / simulation_time
        flow = finished_jobs[i] / simulation_time
        average_jobs = job_area[i] / simulation_time
        system_average_jobs += average_jobs
        if finished_jobs[i] == 0:
            response_time_ms = 0.0
        else:
            response_time_seconds = response_sum[i] / finished_jobs[i]
            response_time_ms = response_time_seconds * 1000
        rows.append({
            "K": k,
            "r": r,
            "alpha": alpha,
            "node": names[i],
            "U": utilization,
            "X": flow,
            "J": average_jobs,
            "T_ms": response_time_ms
        })
    #Rezultati za cijeli sistem
    system_flow = system_finished / simulation_time
    if system_finished == 0:
        system_response_time_ms = 0.0
    else:
        system_response_time_seconds = system_response_sum / system_finished
        system_response_time_ms = system_response_time_seconds * 1000
    rows.append({
        "K": k,
        "r": r,
        "alpha": alpha,
        "node": "SYSTEM",
        "U": "",
        "X": system_flow,
        "J": system_average_jobs,
        "T_ms": system_response_time_ms
    })
    return rows


def run_one_task(task):
    k = task[0]
    r = task[1]
    alpha = task[2]
    seed = task[3]
    simulation_time = task[4]
    return simulate(k, r, alpha, seed, simulation_time)


def average_results(runs):
    average_rows = []
    number_of_rows = len(runs[0])
    #Usrednjavaju se isti redovi svih simulacija
    for row_index in range(number_of_rows):
        first_row = runs[0][row_index]
        utilization_sum = 0.0
        flow_sum = 0.0
        jobs_sum = 0.0
        time_sum = 0.0
        has_utilization = first_row["U"] != ""
        for run in runs:
            row = run[row_index]
            if has_utilization:
                utilization_sum += row["U"]
            flow_sum += row["X"]
            jobs_sum += row["J"]
            time_sum += row["T_ms"]
        if has_utilization:
            average_utilization = utilization_sum / len(runs)
        else:
            average_utilization = ""
        average_rows.append({
            "K": first_row["K"],
            "r": first_row["r"],
            "alpha": first_row["alpha"],
            "node": first_row["node"],
            "U": average_utilization,
            "X": flow_sum / len(runs),
            "J": jobs_sum / len(runs),
            "T_ms": time_sum / len(runs)
        })
    return average_rows


def write_simulation_file(filename, rows):
    path = os.path.join(RESULTS_FOLDER, filename)
    file = open(path, "w", newline="", encoding="utf-8")
    writer = csv.writer(file)
    writer.writerow([
        "K",
        "r",
        "alpha_jobs_per_s",
        "node",
        "U",
        "X_jobs_per_s",
        "J",
        "T_ms"
    ])
    for row in rows:
        if row["U"] == "":
            utilization = ""
        else:
            utilization = round(row["U"], 10)
        writer.writerow([
            row["K"],
            row["r"],
            round(row["alpha"], 10),
            row["node"],
            utilization,
            round(row["X"], 10),
            round(row["J"], 10),
            round(row["T_ms"], 10)
        ])
    file.close()


def run_simulations(simulation_time):
    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    single_results = []
    tasks = []
    group_starts = []
    seed = 1000
    for k in K_VALUES:
        names, times, visit_ratios, alpha_max, critical_resources = calculate_basic_data(k)
        for r in R_VALUES:
            alpha = r * alpha_max
            #Jedna pojedinačna simulacija
            one_result = simulate(k, r, alpha, seed, simulation_time)
            single_results.extend(one_result)
            seed += 1
            #Pamti se početak grupe od 100 simulacija
            group_starts.append(len(tasks))
            for i in range(NUMBER_OF_SIMULATIONS):
                task = (k, r, alpha, seed, simulation_time)
                tasks.append(task)
                seed += 1
    print()
    print("Pokrećem ponovljene simulacije")
    #Simulacije se pokreću paralelno
    with ProcessPoolExecutor() as pool:
        all_runs = list(pool.map(run_one_task, tasks))
    average_rows = []
    for start in group_starts:
        end = start + NUMBER_OF_SIMULATIONS
        runs_for_same_parameters = all_runs[start:end]
        average_rows.extend(average_results(runs_for_same_parameters))
    write_simulation_file("rezultati_simulacija.csv", single_results)
    write_simulation_file(
        "rezultati_simulacija_usrednjeno.csv",
        average_rows
    )
    print("Simulacioni fajlovi su napravljeni")