from analytical import run_analytical
from simulation import run_simulations
from comparison import run_comparison
from params import SIMULATION_TIME

if __name__ == "__main__":
    minutes_input = input(
        "Trajanje simulacije u minutima "
        "(Enter za podrazumevanih 30): "
    )
    if minutes_input.strip() == "":
        simulation_time = SIMULATION_TIME
    else:
        simulation_time = float(minutes_input) * 60

    run_analytical()
    run_simulations(simulation_time)
    run_comparison()