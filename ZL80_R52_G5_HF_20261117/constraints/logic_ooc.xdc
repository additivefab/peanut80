# Logic-clock design assumption for normalized core only.
# This file contains NO physical ADC/DCO timing or approved board IO constraints.
create_clock -name logic_clk -period 10.000 [get_ports clk]
# Other inputs are normalized-internal logic contracts or asynchronous observations.
# OOC reports MUST retain unconstrained input findings; do not silence them globally.
