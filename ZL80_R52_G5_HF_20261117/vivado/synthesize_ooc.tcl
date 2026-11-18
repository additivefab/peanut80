# Synthesis checks only: NO IO mapping, place/route, bitstream or hardware connection.
if {$argc != 1} {error "Provide verified FPGA part via -tclargs"}
set part [lindex $argv 0]
set root [file normalize [file join [file dirname [info script]] ..]]
set out [file join $root validation results vivado_ooc]
if {[file exists $out]} {error "Refusing to overwrite previous OOC evidence"}
file mkdir $out
set files [concat [glob [file join $root rtl core *.sv]] [glob [file join $root rtl helpers *.sv]]]
read_verilog -sv $files
synth_design -top zl80_capture_core -part $part -mode out_of_context
read_xdc [file join $root constraints logic_ooc.xdc]
report_utilization -file [file join $out utilization.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
report_timing_summary -file [file join $out timing_summary_PRE_ROUTE.rpt]
report_cdc -details -file [file join $out cdc_PRE_INTEGRATION.rpt]
write_checkpoint [file join $out normalized_core_SYNTH_ONLY.dcp]
puts "OOC checkpoint created; this is not placed/routed and not a deployable FPGA design."
