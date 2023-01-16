#
# Copyright 2018-2019 Ettus Research, a National Instruments Brand
#

# NOTE: All comments prefixed with a "##" will be displayed as a part of the "make help" target
##-------------------
##USRP E3XX FPGA Help
##-------------------
##Usage:
## make <Targets> <Options>
##
##Output:
## $(CUSTOM_BUILD_DIR)/build/usrp_<product>_fpga_<image_type>.bit:    Configuration bitstream with header
## $(CUSTOM_BUILD_DIR)/build/usrp_<product>_fpga_<image_type>.dts:    Device tree source file
## $(CUSTOM_BUILD_DIR)/build/usrp_<product>_fpga_<image_type>.rpt:    Build report (includes utilization and timing summary)

# Option to build and output the bitstreams in different directories. It's complementary to the BUILD_BASE_DIR option
CUSTOM_BUILD_DIR ?= .
# Base output directory for all builds.
BUILD_BASE_DIR ?= $(CUSTOM_BUILD_DIR)

# Initialize a build seed. This can be changed to randomly affect build results.
BUILD_SEED ?= 0

1G_DEFS=SFP_1GBE=1   BUILD_1G=1     $(OPTIONS) BUILD_SEED=$(BUILD_SEED)
XG_DEFS=SFP_10GBE=1  BUILD_10G=1    $(OPTIONS) BUILD_SEED=$(BUILD_SEED)
AA_DEFS=SFP_AURORA=1 BUILD_AURORA=1 $(OPTIONS) BUILD_SEED=$(BUILD_SEED)

# Set build option (check RTL, run synthesis, or do a full build)
ifndef TARGET
	ifdef CHECK
		TARGET = rtl
	else ifdef SYNTH
		TARGET = synth
	else ifdef IPONLY
		TARGET = viv_ip
	else
		TARGET = bin
	endif
endif
TOP ?= e320

DEFAULT_IMAGE_CORE_FILE_E320=e320_rfnoc_image_core.v
DEFAULT_EDGE_FILE_E320=$(abspath e320_static_router.hex)

# vivado_build($1=Device, $2=Definitions)
vivado_build = make -f Makefile.e320.inc $(TARGET) NAME=$@ ARCH=$(XIL_ARCH_$1) PART_ID=$(XIL_PART_ID_$1) $2 TOP_MODULE=$(TOP) EXTRA_DEFS="$2" DEFAULT_RFNOC_IMAGE_CORE_FILE=$(DEFAULT_IMAGE_CORE_FILE_$1) DEFAULT_EDGE_FILE=$(DEFAULT_EDGE_FILE_$1)
vivado_ip    = make -f Makefile.e320.inc viv_ip    NAME=$@ ARCH=$(XIL_ARCH_$1) PART_ID=$(XIL_PART_ID_$1) $2 TOP_MODULE=$(TOP) EXTRA_DEFS="$2" DEFAULT_RFNOC_IMAGE_CORE_FILE=$(DEFAULT_IMAGE_CORE_FILE_$1) DEFAULT_EDGE_FILE=$(DEFAULT_EDGE_FILE_$1)

# post_build($1=Device, $2=Option)
ifeq ($(TARGET),bin)
	post_build = @\
		mkdir -p $(CUSTOM_BUILD_DIR)/build; \
		echo "Exporting bitstream file..."; \
		cp $(BUILD_BASE_DIR)/build-$(1)_$(2)/e320.bit $(CUSTOM_BUILD_DIR)/build/usrp_`echo $(1) | tr A-Z a-z`_fpga_$(2).bit; \
		echo "Exporting build report..."; \
		cp $(BUILD_BASE_DIR)/build-$(1)_$(2)/build.rpt $(CUSTOM_BUILD_DIR)/build/usrp_`echo $(1) | tr A-Z a-z`_fpga_$(2).rpt; \
		echo "Build DONE ... $(1)_$(2)";
else
	post_build = @echo "Skipping bitfile export."
endif

##
##Supported Targets
##-----------------

all:      E320_1G E320_XG ##(Default target)

##E320_IP:  Build IP for E320 only.
E320_IP:
	+$(call vivado_ip,E320,$(XG_DEFS) E320=1)

##E320_1G:  1GigE on SFP+ Port.
E320_1G: E320_IP $(CUSTOM_BUILD_DIR)/build/usrp_e320_fpga_1G.dts
	$(call vivado_build,E320,$(1G_DEFS) E320=1)
	$(call post_build,E320,1G)

##E320_XG:  10GigE on SFP+ Port.
E320_XG: E320_IP $(CUSTOM_BUILD_DIR)/build/usrp_e320_fpga_XG.dts
	$(call vivado_build,E320,$(XG_DEFS) E320=1)
	$(call post_build,E320,XG)

##E320_AA:  Aurora on SFP+ Port.
E320_AA: E320_IP $(CUSTOM_BUILD_DIR)/build/usrp_e320_fpga_AA.dts
	$(call vivado_build,E320,$(AA_DEFS) E320=1)
	$(call post_build,E320,AA)


$(CUSTOM_BUILD_DIR)/build/%.dts: dts/%.dts dts/*.dtsi
	-mkdir -p $(CUSTOM_BUILD_DIR)/build
	${CC} -o $@ -E -I dts -nostdinc -undef -x assembler-with-cpp -D__DTS__ $<

clean:    ##Clean up all target build outputs.
	@echo "Cleaning targets..."
	@rm -rf $(BUILD_BASE_DIR)/build-E3*_*
	@rm -rf $(CUSTOM_BUILD_DIR)/build

cleanall: ##Clean up all target and ip build outputs.
	@echo "Cleaning targets and IP..."
	@rm -rf build-ip
	@rm -rf $(BUILD_BASE_DIR)/build-E3*_*
	@rm -rf $(CUSTOM_BUILD_DIR)/build

help:     ##Show this help message.
	@grep -h "##" Makefile | grep -v "\"##\"" | sed -e 's/\\$$//' | sed -e 's/##//'

##
##Supported Options
##-----------------
##GUI=1          Launch the build in the Vivado GUI.
##CHECK=1        Launch the syntax checker instead of building a bitfile.
##SYNTH=1        Launch the build but stop after synthesis.
##IPONLY=1       Launch the build of the required IPs only.
##SAVE=1         Save Vivado project, otherwise it's created in memory.
##CUSTOM_BUILD_DIR=<path>     Path to custom bitstream building directory
##BUILD_SEED=<N> Build seed to used to affect build results. (Default is 0)
##TOP=<module>   Specify a top module for syntax checking. (Optional. Default is the bitfile top)

.PHONY: all clean cleanall help
