set sigs [list pipeline_evidence_tb.clk pipeline_evidence_tb.rst pipeline_evidence_tb.cpu.id_valid pipeline_evidence_tb.cpu.ex_valid pipeline_evidence_tb.cpu.mem_valid pipeline_evidence_tb.cpu.wb_valid pipeline_evidence_tb.cpu.ex_load_hazard pipeline_evidence_tb.cpu.id_go pipeline_evidence_tb.cpu.ex_go pipeline_evidence_tb.cpu.ex_redirect pipeline_evidence_tb.cpu.ex_pc pipeline_evidence_tb.cpu.id_pc pipeline_evidence_tb.rv pipeline_evidence_tb.rpc pipeline_evidence_tb.rrd pipeline_evidence_tb.value]
gtkwave::addSignalsFromList $sigs
gtkwave::/Edit/Set_Trace_Max_Hier 1
gtkwave::/Time/Zoom/Zoom_Full
gtkwave::setMarker 240000
