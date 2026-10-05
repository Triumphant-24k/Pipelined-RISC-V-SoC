ENTRY(_start)
SECTIONS {
 . = 0; .text : { *(.text.start) *(.text*) }
 .rodata : { *(.rodata*) }
 .data : { *(.data*) *(.sdata*) }
 .bss : { *(.bss*) *(.sbss*) *(COMMON) }
 _end = .;
 ASSERT(_end < 0x30000, "firmware exceeds memory")
}
