# Keep real input isolation buffers close to package-facing core pins.
# First call precedes global placement; second call also anchors the CTS root.
proc pin_input_buffers {} {
 set block [ord::get_db_block]
 set reserved [dict create]
 set candidates {}
 foreach term [$block getBTerms] {
  if {[$term getIoType] ne "INPUT"} {continue}
  set its [[$term getNet] getITerms]
  if {[llength $its] != 1} {continue}
  set inst [[lindex $its 0] getInst]
  set master [[$inst getMaster] getName]
  if {![string match BUF_X* $master] && ![string match CLKBUF_X* $master]} {continue}
  set name [$inst getName]
  set_dont_touch [get_cells $name]
  lappend candidates [list [$term getName] $term $inst]
  if {[$inst isFixed]} {
   set box [$inst getBBox]
   dict lappend reserved [$box yMin] [list [$box xMin] [$box xMax]]
  }
 }
 foreach candidate [lsort -index 0 $candidates] {
  lassign $candidate port term inst
  if {[$inst isFixed]} {continue}
  lassign [$term getFirstPinLocation] placed px py
  if {!$placed} {error "No location for input $port"}
  set width [[$inst getMaster] getWidth]
  set height [[$inst getMaster] getHeight]
  set best_cost 1e30
  foreach row [$block getRows] {
   lassign [$row getOrigin] rx ry
   set step [$row getSpacing]
   set xmax [expr {$rx+[$row getSiteCount]*$step-$width-$step}]
   set xmin [expr {$rx+$step}]
   set target [expr {int(round(double($px-$width/2-$rx)/$step))*$step+$rx}]
   for {set shift -8} {$shift<=8} {incr shift} {
    set x [expr {max($xmin,min($xmax,$target+$shift*$step))}]
    set overlap 0
    if {[dict exists $reserved $ry]} {
     foreach interval [dict get $reserved $ry] {
      lassign $interval a b
      if {$x < $b+$step && $x+$width > $a-$step} {set overlap 1;break}
     }
    }
    if {$overlap} {continue}
    set cost [expr {abs($x+$width/2-$px)+abs($ry+$height/2-$py)}]
    if {$cost<$best_cost} {set best_cost $cost;set best [list $x $ry [$row getOrient]]}
   }
  }
  if {$best_cost==1e30} {error "No legal edge site for $port"}
  lassign $best x y orient
  $inst setOrient $orient
  $inst setLocation $x $y
  $inst setPlacementStatus FIRM
  dict lappend reserved $y [list $x [expr {$x+$width}]]
  puts "INPUT_ANCHOR $port [$inst getName] [[$inst getMaster] getName] $x $y distance_dbu=$best_cost"
 }
}
