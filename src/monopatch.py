def patch(name, path):
    return {
        ## IMPORTANT:
        ## THE DIFF FORMAT REQUIRES COMMON TEXT TO BE PLACED BOTH ABOVE AND BELLOW CHANGED TEXT
        ## THIS IS VALID
        ##   original
        ## - remove
        ## + add
        ##  original
        ## THIS IS NOT
        ##   original
        ## - remove
        ## + add
        ## NEITHER IS THIS:
        ## - remove
        ## + add
        ##   original
        "pulp_soc": f"""
--- a/Bender.yml
+++ b/Bender.yml
@@ -50,2 +50,3 @@ dependencies:
   register_interface:     {{ git: "https://github.com/pulp-platform/register_interface.git", version: 0.3.1 }}
+  {name}:                   {{ path: "{path}"}}

--- a/rtl/pulp_soc/pulp_soc.sv
+++ b/rtl/pulp_soc/pulp_soc.sv
@@ -406,6 +406,11 @@ module pulp_soc import dm::*; #(
         assign base_addr_int = 4'b0001; //FIXME attach this signal somewhere in the soc peripherals --> IGOR
     `endif
 
+    AXI_BUS #(.AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
+              .AXI_DATA_WIDTH(AXI_DATA_OUT_WIDTH),
+              .AXI_ID_WIDTH(AXI_ID_OUT_WIDTH),
+              .AXI_USER_WIDTH(AXI_USER_WIDTH)
+    ) s_{name}_bus();
 
 
     logic s_rstn_cluster_sync_soc;
@@ -855,9 +860,19 @@ module pulp_soc import dm::*; #(
         .apb_peripheral_bus    ( s_apb_periph_bus    ),
         .l2_interleaved_slaves ( s_mem_l2_bus        ),
         .l2_private_slaves     ( s_mem_l2_pri_bus    ),
-        .boot_rom_slave        ( s_mem_rom_bus       )
+        .boot_rom_slave        ( s_mem_rom_bus       ),
+        .{name}_slave      ( s_{name}_bus    )
         );
-
+    {name}_top #(
+        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
+        .AXI_ID_WIDTH(AXI_ID_OUT_WIDTH),
+        .AXI_USER_WIDTH(AXI_USER_WIDTH)
+        ) i_{name} (
+        .clk_i(s_soc_clk),
+        .rst_ni(s_soc_rstn),
+        .test_mode_i(dft_test_mode_i),
+        .axi_slave(s_{name}_bus)
+    );
     /* Debug Subsystem */
 
     dmi_jtag #(
@@ -937,9 +952,8 @@ module pulp_soc import dm::*; #(
     );
     assign s_lint_riscv_jtag_bus.wen = ~lint_riscv_jtag_bus_master_we;
 
-    jtag_tap_top  #(
-        .IDCODE_VALUE             ( `PULP_JTAG_IDCODE  )
-    ) jtag_tap_top_i (
+    jtag_tap_top jtag_tap_top_i
+    (
         .tck_i                    ( jtag_tck_i         ),
         .trst_ni                  ( jtag_trst_ni       ),
         .tms_i                    ( jtag_tms_i         ),
--- a/rtl/pulp_soc/soc_interconnect.sv
+++ b/rtl/pulp_soc/soc_interconnect.sv
@@ -89,11 +89,12 @@ module soc_interconnect
     ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
 
 
-    XBAR_TCDM_BUS l2_demux_slaves[NR_MASTER_PORTS*3]();
     for (genvar i = 0; i < NR_MASTER_PORTS; i++) begin : gen_l2_demux
-        `TCDM_ASSIGN_INTF(l2_demux_2_axi_bridge[i], l2_demux_slaves[3*i + 0]);
-        `TCDM_ASSIGN_INTF(l2_demux_2_contiguous_xbar[i], l2_demux_slaves[3*i + 1]);
-        `TCDM_ASSIGN_INTF(l2_demux_2_interleaved_xbar[i], l2_demux_slaves[3*i + 2]);
+        XBAR_TCDM_BUS demux_slaves[3]();
+
+        `TCDM_ASSIGN_INTF(l2_demux_2_axi_bridge[i], demux_slaves[0]);
+        `TCDM_ASSIGN_INTF(l2_demux_2_contiguous_xbar[i], demux_slaves[1]);
+        `TCDM_ASSIGN_INTF(l2_demux_2_interleaved_xbar[i], demux_slaves[2]);
 
 
         tcdm_demux #(
@@ -105,7 +106,7 @@ module soc_interconnect
                                   .test_en_i,
                                   .addr_map_rules(addr_space_l2_demux),
                                   .master_port(master_ports[i]),
-                                  .slave_ports(l2_demux_slaves[3*i:3*(i+1)-1])
+                                  .slave_ports(demux_slaves)
                                   );
     end
 
@@ -116,13 +117,14 @@ module soc_interconnect
     // interleaved memory region.                                                                               //
     //////////////////////////////////////////////////////////////////////////////////////////////////////////////
     XBAR_TCDM_BUS master_ports_interleaved_only_checked[NR_MASTER_PORTS_INTERLEAVED_ONLY]();
-    XBAR_TCDM_BUS err_demux_slaves[NR_MASTER_PORTS_INTERLEAVED_ONLY*2]();
     for (genvar i = 0; i < NR_MASTER_PORTS_INTERLEAVED_ONLY; i++) begin : gen_interleaved_only_err_checkers
-        `TCDM_ASSIGN_INTF(master_ports_interleaved_only_checked[i], err_demux_slaves[2*i + 1]);
+        XBAR_TCDM_BUS err_demux_slaves[2]();
+
+        `TCDM_ASSIGN_INTF(master_ports_interleaved_only_checked[i], err_demux_slaves[1]);
         // Workaround for genus (doesn't seem to like references interface
         // arrays in port connections so we assign it to a scalar interface instance)
         XBAR_TCDM_BUS err_slave();
-        `TCDM_ASSIGN_INTF(err_slave, err_demux_slaves[2*i + 0]);
+        `TCDM_ASSIGN_INTF(err_slave, err_demux_slaves[0]);
 
         //The tcdm demux will route all transaction that do not match any addr rule to port 0 (which we connect to an
         //error slave)
@@ -135,7 +137,7 @@ module soc_interconnect
           .test_en_i,
           .addr_map_rules ( addr_space_interleaved           ),
           .master_port    ( master_ports_interleaved_only[i] ),
-          .slave_ports    ( err_demux_slaves[2*i:2*(i+1)-1]  )
+          .slave_ports    ( err_demux_slaves                 )
         );
         tcdm_error_slave #(
           .ERROR_RESPONSE(32'hBADACCE5)
--- a/rtl/pulp_soc/soc_interconnect_wrap.sv
+++ b/rtl/pulp_soc/soc_interconnect_wrap.sv
@@ -56,7 +56,8 @@ module soc_interconnect_wrap
        APB_BUS.Master           apb_peripheral_bus, // Connects to all the SoC Peripherals
        XBAR_TCDM_BUS.Master     l2_interleaved_slaves[NR_L2_PORTS], // Connects to the interleaved memory banks
        XBAR_TCDM_BUS.Master     l2_private_slaves[2], // Connects to core-private memory banks
-       XBAR_TCDM_BUS.Master     boot_rom_slave //Connects to the bootrom
+       XBAR_TCDM_BUS.Master     boot_rom_slave, //Connects to the bootrom
+       AXI_BUS.Master           {name}_slave //connects to alu
      );
 
     //**Do not change these values unles you verified that all downstream IPs are properly parametrized and support it**
@@ -109,11 +110,11 @@ module soc_interconnect_wrap
         '{{ idx: 1 , start_addr: `SOC_MEM_MAP_PRIVATE_BANK1_START_ADDR , end_addr: `SOC_MEM_MAP_PRIVATE_BANK1_END_ADDR}} ,
         '{{ idx: 2 , start_addr: `SOC_MEM_MAP_BOOT_ROM_START_ADDR      , end_addr: `SOC_MEM_MAP_BOOT_ROM_END_ADDR}}}};
 
-    localparam NR_RULES_AXI_CROSSBAR = 2;
+    localparam NR_RULES_AXI_CROSSBAR = 3;
     localparam addr_map_rule_t [NR_RULES_AXI_CROSSBAR-1:0] AXI_CROSSBAR_RULES = '{{
        '{{ idx: 0, start_addr: `SOC_MEM_MAP_AXI_PLUG_START_ADDR,    end_addr: `SOC_MEM_MAP_AXI_PLUG_END_ADDR}},
-       '{{ idx: 1, start_addr: `SOC_MEM_MAP_PERIPHERALS_START_ADDR, end_addr: `SOC_MEM_MAP_PERIPHERALS_END_ADDR}}}};
-
+       '{{ idx: 1, start_addr: `SOC_MEM_MAP_PERIPHERALS_START_ADDR, end_addr: `SOC_MEM_MAP_PERIPHERALS_END_ADDR}},
+       '{{ idx: 2, start_addr: `SOC_MEM_MAP_{name.upper()}_START_ADDR, end_addr: `SOC_MEM_MAP_{name.upper()}_END_ADDR}};
     //For legacy reasons, the fc_data port can alias the address prefix 0x000 to 0x1c0. E.g. an access to 0x00001234 is
     //mapped to 0x1c001234. The following lines perform this remapping.
     XBAR_TCDM_BUS tcdm_fc_data_addr_remapped();
@@ -175,9 +176,10 @@ module soc_interconnect_wrap
               .AXI_DATA_WIDTH(32),
               .AXI_ID_WIDTH(pkg_soc_interconnect::AXI_ID_OUT_WIDTH),
               .AXI_USER_WIDTH(AXI_USER_WIDTH)
-              ) axi_slaves[2]();
+              ) axi_slaves[3]();
     `AXI_ASSIGN(axi_slave_plug, axi_slaves[0])
     `AXI_ASSIGN(axi_to_axi_lite_bridge, axi_slaves[1])
+    `AXI_ASSIGN({name}_slave, axi_slaves[2])
 
     //Interconnect instantiation
     soc_interconnect #(
@@ -191,7 +193,7 @@ module soc_interconnect_wrap
                        .NR_SLAVE_PORTS_CONTIG(3), // Bootrom + number of private memory banks (normally 1 for
                                                   // programm instructions and 1 for programm stack )
                        .NR_ADDR_RULES_SLAVE_PORTS_CONTIG(NR_RULES_CONTIG_CROSSBAR),
-                       .NR_AXI_SLAVE_PORTS(2), // 1 for AXI to cluster, 1 for SoC peripherals (converted to APB)
+                       .NR_AXI_SLAVE_PORTS(3), // 1 for AXI to cluster, 1 for SoC peripherals (converted to APB)
                        .NR_ADDR_RULES_AXI_SLAVE_PORTS(NR_RULES_AXI_CROSSBAR),
                        .AXI_MASTER_ID_WIDTH(1), //Doesn't need to be changed. All axi masters in the current
                                                 //interconnect come from a TCDM protocol converter and thus do not have and AXI ID.
""",
        "pulp-runtime": f"""
--- a/include/archi/chips/pulpissimo/memory_map.h
+++ b/include/archi/chips/pulpissimo/memory_map.h
@@ -77,5 +77,6 @@
 #define ARCHI_CLUSTER_PERIPHERALS_ADDR             ( ARCHI_CLUSTER_ADDR + ARCHI_CLUSTER_PERIPHERALS_OFFSET )
 #define ARCHI_CLUSTER_PERIPHERALS_GLOBAL_ADDR(cid) ( ARCHI_CLUSTER_GLOBAL_ADDR(cid) + ARCHI_CLUSTER_PERIPHERALS_OFFSET )
 
+#define {name.upper()}0_BASE_ADDR 0x1a400000
 
 #endif
--- a/include/pulp.h
+++ b/include/pulp.h
@@ -27,6 +27,8 @@
 #include <archi/pulp.h>
 #include <hal/pulp.h>
 #include <data/data.h>
+#include <{name}_auto.h>
+#include <{name}_driver.h>
 
 typedef enum {{
   PI_FREQ_DOMAIN_FC     = 0,
--- a/rules/pulpos/targets/pulpissimo.mk
+++ b/rules/pulpos/targets/pulpissimo.mk
@@ -57,7 +57,7 @@ soc_eu/version=2
 PULP_SRCS     += kernel/fll-v$(fll/version).c
 PULP_SRCS     += kernel/freq-domains.c
 PULP_SRCS     += kernel/chips/pulpissimo/soc.c
-
+PULP_SRCS     += drivers/{name}_driver.c
 
 include $(PULPRT_HOME)/rules/pulpos/configs/default.mk
 
""",
    }
