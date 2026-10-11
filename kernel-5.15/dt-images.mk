# Source-built DTB and DTBO share the exact kernel configuration/output.
ifndef ALIOTH_KERNEL_515_DT_RULES
ALIOTH_KERNEL_515_DT_RULES := true
# Track real sources so Ninja can invoke incremental Kbuild after driver edits.
# Generated external .mod.c files must not become source dependencies.
ALIOTH_KERNEL_515_SOURCE_DEPS := $(shell find $(KERNEL_SRC) kernel-research/alioth-5.15/sources/vendor/qcom/opensource -name .git -prune -o -type f ! -name '*.mod.c' \( -name '*.c' -o -name '*.h' -o -name '*.S' -o -name '*.dts' -o -name '*.dtsi' -o -name 'Kconfig*' -o -name 'Makefile*' -o -name 'Kbuild*' -o -name '*.sh' -o -name '*.py' -o -name '*.conf' -o -name '*.lds' \) -print)
ALIOTH_KERNEL_515_GIT_DIR := $(shell git -C $(KERNEL_SRC) rev-parse --absolute-git-dir)
ALIOTH_KERNEL_515_GIT_REF := $(shell git -C $(KERNEL_SRC) symbolic-ref -q HEAD)
ALIOTH_KERNEL_515_GIT_DEPS := $(wildcard $(ALIOTH_KERNEL_515_GIT_DIR)/HEAD $(ALIOTH_KERNEL_515_GIT_DIR)/packed-refs $(if $(ALIOTH_KERNEL_515_GIT_REF),$(ALIOTH_KERNEL_515_GIT_DIR)/$(ALIOTH_KERNEL_515_GIT_REF)))
ALIOTH_KERNEL_515_LLVM_DEPS := $(addprefix $(TARGET_KERNEL_CLANG_PATH)/bin/,clang ld.lld llvm-ar llvm-nm llvm-objcopy llvm-strip)
$(KERNEL_CONFIG): $(ALIOTH_KERNEL_515_LLVM_DEPS)
$(TARGET_PREBUILT_INT_KERNEL): $(ALIOTH_KERNEL_515_SOURCE_DEPS) $(ALIOTH_KERNEL_515_GIT_DEPS) $(ALIOTH_KERNEL_515_LLVM_DEPS) $(ALIOTH_KERNEL_515_PATH)/external/Makefile $(ALIOTH_KERNEL_515_PATH)/external/build.py $(ALIOTH_KERNEL_515_PATH)/modules.mk
ALIOTH_KERNEL_515_DTB := $(KERNEL_OUT)/arch/arm64/boot/dts/qcom/sm8250-xiaomi-alioth.dtb
$(INSTALLED_DTBIMAGE_TARGET): $(TARGET_PREBUILT_INT_KERNEL) $(HOST_OUT_EXECUTABLES)/fdtput
	mkdir -p $(dir $@)
	cp $(ALIOTH_KERNEL_515_DTB) $@
	$(HOST_OUT_EXECUTABLES)/fdtput -t x $@ / qcom,board-id 0 0
$(BOARD_PREBUILT_DTBOIMAGE): $(TARGET_PREBUILT_INT_KERNEL) $(DTC) $(HOST_OUT_EXECUTABLES)/mkdtimg $(ALIOTH_KERNEL_515_PATH)/alioth-overlay.dts
	mkdir -p $(dir $@)
	$(DTC) -@ -I dts -O dtb -o $(dir $@)/alioth.dtbo $(ALIOTH_KERNEL_515_PATH)/alioth-overlay.dts
	$(HOST_OUT_EXECUTABLES)/mkdtimg create $@ --page_size=4096 --id=0 --rev=0 $(dir $@)/alioth.dtbo
endif
