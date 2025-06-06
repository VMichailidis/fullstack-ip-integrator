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
@@ -34,2 +34,3 @@ dependencies:
   register_interface:     {{ git: "https://github.com/pulp-platform/register_interface.git", version: 0.4.1 }}
+  {name}:                   {{ path: "{path}"}}

--- a/rtl/pulp_soc/pulp_soc.sv
+++ b/rtl/pulp_soc/pulp_soc.sv
@@ -410,3 +410,8 @@
   ) s_data_in_bus ();

+    AXI_BUS #(.AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
+              .AXI_DATA_WIDTH(AXI_DATA_OUT_WIDTH),
+              .AXI_ID_WIDTH(AXI_ID_OUT_WIDTH),
+              .AXI_USER_WIDTH(AXI_USER_WIDTH)
+    ) s_{name}_bus();
 
@@ -807,8 +807,19 @@
     .l2_interleaved_slaves   ( s_mem_l2_bus        ),
     .l2_private_slaves       ( s_mem_l2_pri_bus    ),
-    .boot_rom_slave          ( s_mem_rom_bus       )
+    .boot_rom_slave          ( s_mem_rom_bus       ),
+    .{name}_slave      ( s_{name}_bus    )
   );
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
--- a/rtl/pulp_soc/soc_interconnect_wrap.sv
+++ b/rtl/pulp_soc/soc_interconnect_wrap.sv
@@ -57,7 +57,8 @@ module soc_interconnect_wrap
        XBAR_TCDM_BUS.Master     l2_interleaved_slaves[NR_L2_PORTS], // Connects to the interleaved memory banks
        XBAR_TCDM_BUS.Master     l2_private_slaves[2], // Connects to core-private memory banks
-       XBAR_TCDM_BUS.Master     boot_rom_slave //Connects to the bootrom
+       XBAR_TCDM_BUS.Master     boot_rom_slave, //Connects to the bootrom
+       AXI_BUS.Master           {name}_slave //connects to alu
      );
 
     //**Do not change these values unles you verified that all downstream IPs are properly parametrized and support it**
@@ -122,11 +122,11 @@
         '{{ idx: 1 , start_addr: `SOC_MEM_MAP_PRIVATE_BANK1_START_ADDR , end_addr: `SOC_MEM_MAP_PRIVATE_BANK1_END_ADDR}} ,
         '{{ idx: 2 , start_addr: `SOC_MEM_MAP_BOOT_ROM_START_ADDR      , end_addr: `SOC_MEM_MAP_BOOT_ROM_END_ADDR}}}};
 
-    localparam NR_RULES_AXI_CROSSBAR = 2;
+    localparam NR_RULES_AXI_CROSSBAR = 3;
     localparam addr_map_rule_t [NR_RULES_AXI_CROSSBAR-1:0] AXI_CROSSBAR_RULES = '{{
        '{{ idx: 0, start_addr: `SOC_MEM_MAP_AXI_PLUG_START_ADDR,    end_addr: `SOC_MEM_MAP_AXI_PLUG_END_ADDR}},
-       '{{ idx: 1, start_addr: `SOC_MEM_MAP_PERIPHERALS_START_ADDR, end_addr: `SOC_MEM_MAP_PERIPHERALS_END_ADDR}}}};
-
+       '{{ idx: 1, start_addr: `SOC_MEM_MAP_PERIPHERALS_START_ADDR, end_addr: `SOC_MEM_MAP_PERIPHERALS_END_ADDR}},
+       '{{ idx: 2, start_addr: `SOC_MEM_MAP_{name.upper()}_START_ADDR, end_addr: `SOC_MEM_MAP_{name.upper()}_END_ADDR}}}};
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
