# Typical-corner educational target: 100 MHz; all delays in ns.
create_clock -name core_clk -period 10.0 [get_ports clk]
# Distinct jitter/margin assumptions: setup 200 ps, hold 50 ps.
set_clock_uncertainty -setup 0.2 [get_clocks core_clk]
set_clock_uncertainty -hold 0.05 [get_clocks core_clk]
set_clock_transition 0.1 [get_clocks core_clk]
set_input_delay 1.0 -clock core_clk [get_ports {rst ir ip insn* ierr dr dp rd* derr timer_irq external_irq}]
set_output_delay 1.0 -clock core_clk [all_outputs]
set_load 0.01 [all_outputs]
set_input_transition 0.1 [get_ports {rst ir ip insn* ierr dr dp rd* derr timer_irq external_irq}]
