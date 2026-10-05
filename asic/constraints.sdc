# Initial 100 MHz design target. This is a constraint, not a measured frequency.
create_clock -name core_clk -period 10.0 [get_ports clk]
set_clock_uncertainty 0.2 [get_clocks core_clk]
set_input_delay 1.0 -clock core_clk [remove_from_collection [all_inputs] [get_ports clk]]
set_output_delay 1.0 -clock core_clk [all_outputs]
set_load 0.05 [all_outputs]
