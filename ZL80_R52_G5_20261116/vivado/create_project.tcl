# Review/simulation project only. Verify actual silicon part before supplying argument.
if {$argc != 1} { error "Usage: -tclargs <verified-part>, e.g. xc7z020clg484-1 (example only)" }
set part [lindex $argv 0]
if {[llength [get_parts -quiet $part]] != 1} {error "Device part unavailable: $part"}
set root [file normalize [file join [file dirname [info script]] ..]]
set project_dir [file join $root build vivado_review]
if {[file exists $project_dir]} {error "Project already exists; preserve evidence or choose a new workspace."}
create_project zl80_g5_review $project_dir -part $part
set_property target_language Verilog [current_project]
set sv [concat [glob [file join $root rtl core *.sv]] [glob [file join $root rtl helpers *.sv]] [glob [file join $root rtl frontend_candidates *.sv]]]
add_files -norecurse $sv
set_property top zl80_capture_core [current_fileset]
add_files -fileset constrs_1 [file join $root constraints logic_ooc.xdc]
add_files -fileset sim_1 [glob [file join $root sim tb *.sv]]
set_property top tb_capture_core [get_filesets sim_1]
update_compile_order -fileset sources_1
puts "Created REVIEW project only. No board top, PS/DDR/DMA block design or bitstream."
