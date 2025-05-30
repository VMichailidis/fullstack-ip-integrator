## This file defines the strings which should be converted to patches and applied to the sourcecode of the pulp_soc, pulpissimo and pulp-runtime
## Each definition is a dictionary with the following fields
# module_name is the name of the module that will be added. this patching system assumes that the module name will be placed at pulp-platform/modulename
# repo: the repo this module belongs to
# path: the path of the file that this patch will be applied to
# string: the parametrized string that defines the patch
# *IMPORTANT* before parametrizing the patch string, make sure that all instances of '{'and '}' are replaced with '{{' and '}}' so that the string can be formatted correctly


def patches(module_name):
    module2pulp_soc_path = f"..../{module_name}"  # path of module name relative to pulp_soc for pulpissimo/work_dir/pulp_soc/Bender.yml
    return [
        {
            "repo": "pulp_soc",
            "path": "rtl/pulp_soc/pulp_soc.sv",
            "patch": f"""
--- rtl/pulp_soc/pulp_soc.sv
+++ rtl/pulp_soc/pulp_soc.sv
@@ -406,6 +406,11 @@module pulp_soc import dm::*; #(
         assign base_addr_int = 4'b0001; //FIXME attach this signal somewhere in the soc peripherals --> IGOR
     `endif

+    AXI_BUS #(.AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
+              .AXI_DATA_WIDTH(AXI_DATA_OUT_WIDTH),
+              .AXI_ID_WIDTH(AXI_ID_OUT_WIDTH),
+              .AXI_USER_WIDTH(AXI_USER_WIDTH)
+    ) s_{module_name}_bus();


     logic s_rstn_cluster_sync_soc;
@@ -855,9 +860,19 @@ module pulp_soc import dm::*; #(
         .apb_peripheral_bus    ( s_apb_periph_bus    ),
         .l2_interleaved_slaves ( s_mem_l2_bus        ),
         .l2_private_slaves     ( s_mem_l2_pri_bus    ),
-        .boot_rom_slave        ( s_mem_rom_bus       )
+        .boot_rom_slave        ( s_mem_rom_bus       ),
+        .{module_name}_slave        ( s_{module_name}_bus      )
         );
-
+    {module_name}_top #(
+        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
+        .AXI_ID_WIDTH(AXI_ID_OUT_WIDTH),
+        .AXI_USER_WIDTH(AXI_USER_WIDTH)
+        ) i_{module_name} (
+        .clk_i(s_soc_clk),
+        .rst_ni(s_soc_rstn),
+        .test_mode_i(dft_test_mode_i),
+        .axi_slave(s_{module_name}_bus)
+    );
     /* Debug Subsystem */

     dmi_jtag #(
        """,
        },
        {
            "repo": "pulp_soc",
            "path": "rtl/pulp_soc/soc_interconnect_wrap.sv",
            "patch": f"""
--- rtl/pulp_soc/soc_interconnect_wrap.sv
+++ rtl/pulp_soc/soc_interconnect_wrap.sv
@@ -56,7 +56,8 @@ module soc_interconnect_wrap
        APB_BUS.Master           apb_peripheral_bus, // Connects to all the SoC Peripherals
        XBAR_TCDM_BUS.Master     l2_interleaved_slaves[NR_L2_PORTS], // Connects to the interleaved memory banks
        XBAR_TCDM_BUS.Master     l2_private_slaves[2], // Connects to core-private memory banks
-       XBAR_TCDM_BUS.Master     boot_rom_slave //Connects to the bootrom
+       XBAR_TCDM_BUS.Master     boot_rom_slave, //Connects to the bootrom
+       AXI_BUS.Master           {module_name}_slave //connects to alu
      );

     //**Do not change these values unles you verified that all downstream IPs are properly parametrized and support it**
@@ -109,11 +110,11 @@ module soc_interconnect_wrap
         '{{ idx: 1 , start_addr: `SOC_MEM_MAP_PRIVATE_BANK1_START_ADDR , end_addr: `SOC_MEM_MAP_PRIVATE_BANK1_END_ADDR}} ,
         '{{ idx: 2 , start_addr: `SOC_MEM_MAP_BOOT_ROM_START_ADDR      , end_addr: `SOC_MEM_MAP_BOOT_ROM_END_ADDR}};

-    localparam NR_RULES_AXI_CROSSBAR = 2;
+    localparam NR_RULES_AXI_CROSSBAR = 3;
     localparam addr_map_rule_t [NR_RULES_AXI_CROSSBAR-1:0] AXI_CROSSBAR_RULES = '{{
        '{{ idx: 0, start_addr: `SOC_MEM_MAP_AXI_PLUG_START_ADDR,    end_addr: `SOC_MEM_MAP_AXI_PLUG_END_ADDR}},
-       '{{ idx: 1, start_addr: `SOC_MEM_MAP_PERIPHERALS_START_ADDR, end_addr: `SOC_MEM_MAP_PERIPHERALS_END_ADDR}}}};
-
+       '{{ idx: 1, start_addr: `SOC_MEM_MAP_PERIPHERALS_START_ADDR, end_addr: `SOC_MEM_MAP_PERIPHERALS_END_ADDR}},
+       '{{ idx: 2, start_addr: `SOC_MEM_MAP_{module_name.upper()}_START_ADDR, end_addr: `SOC_MEM_MAP_{module_name.upper()}_END_ADDR}}}};
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
+    `AXI_ASSIGN({module_name}_slave, axi_slaves[2])

     //Interconnect instantiation
     soc_interconnect #(
        """,
        },
        {
            "repo": "pulp-runtime",
            "path": "include/archi/chips/pulpissimo/memory_map.h",
            "patch": f"""
--- a/include/archi/chips/pulpissimo/memory_map.h
+++ b/include/archi/chips/pulpissimo/memory_map.h
@@ -77,5 +77,6 @@
 #define ARCHI_CLUSTER_PERIPHERALS_ADDR             ( ARCHI_CLUSTER_ADDR + ARCHI_CLUSTER_PERIPHERALS_OFFSET )
 #define ARCHI_CLUSTER_PERIPHERALS_GLOBAL_ADDR(cid) ( ARCHI_CLUSTER_GLOBAL_ADDR(cid) + ARCHI_CLUSTER_PERIPHERALS_OFFSET )

+#define {module_name.upper()}0_BASE_ADDR 0x1a400000

 #endif
        """,
        },
        {
            "repo": "pulp-runtime",
            "path": "include/pulp.h",
            "patch": f"""
--- a/include/pulp.h
+++ b/include/pulp.h
@@ -27,6 +27,8 @@
 #include <archi/pulp.h>
 #include <hal/pulp.h>
 #include <data/data.h>
+#include <{module_name}_auto.h>
+#include <{module_name}_driver.h>

 typedef enum {{
   PI_FREQ_DOMAIN_FC     = 0,
""",
        },
        {
            "repo": "pulp-runtime",
            "path": "",
            "patch": f"""
--- a/rules/pulpos/targets/pulpissimo.mk
+++ b/rules/pulpos/targets/pulpissimo.mk
@@ -57,7 +57,7 @@ soc_eu/version=2
 PULP_SRCS     += kernel/fll-v$(fll/version).c
 PULP_SRCS     += kernel/freq-domains.c
 PULP_SRCS     += kernel/chips/pulpissimo/soc.c
-
+PULP_SRCS     += drivers/{module_name}_driver.c

 include $(PULPRT_HOME)/rules/pulpos/configs/default.mk
 """,
        },
        {
            "repo": "pulp_soc",
            "path": "Bender.yml",
            "patch": f'''
--- a/Bender.yml
+++ b/Bender.yml
@@ -48,7 +48,8 @@
  hwpe-mac-engine:        {{ git: "https://github.com/pulp-platform/hwpe-mac-engine.git", version: 1.3.3 }}
  riscv-dbg:              {{ git: "https://github.com/pulp-platform/riscv-dbg.git", version: 0.5.0 }}
  register_interface:     {{ git: "https://github.com/pulp-platform/register_interface.git", version: 0.3.1 }}
+ {module_name}:          {{ path: "{module2pulp_soc_path}"}}

 sources:
  # pulp_soc
  - include_dirs:
        ''',
        },
    ]
