# Experimental source-built alioth 5.15; not production ready.
include device/xiaomi/alioth/kernel-5.15/selection.mk
ifeq ($(TARGET_USE_ALIOTH_KERNEL_515),true)
# Native 5.15 uses UFS BSG, rather than the removed vendor query ioctl.
$(call soong_config_set_bool,QTI_GPT_UTILS,USE_BSG_FRAMEWORK,true)
ifneq ($(TARGET_IS_VAB),true)
$(error Alioth 5.15 requires the vendor_boot / VAB partition layout)
endif
ALIOTH_KERNEL_515_PATH := device/xiaomi/alioth/kernel-5.15
TARGET_KERNEL_SOURCE := kernel-research/alioth-5.15/msm-kernel
TARGET_FORCE_PREBUILT_KERNEL :=
TARGET_PREBUILT_KERNEL :=
TARGET_KERNEL_CONFIG := gki_defconfig vendor/kona_GKI.config vendor/xiaomi/sm8250-common.config vendor/xiaomi/alioth.config
TARGET_KERNEL_CONFIG_EXT :=
TARGET_KERNEL_UAPI_AUTO_EXPORTS := true
MERGE_ALL_KERNEL_CONFIGS_AT_ONCE := true
KERNEL_LTO := none
TARGET_KERNEL_CLANG_VERSION := r563880c
TARGET_KERNEL_CLANG_PATH := $(abspath prebuilts/clang/host/linux-x86/clang-$(TARGET_KERNEL_CLANG_VERSION))
TARGET_KERNEL_ADDITIONAL_FLAGS := LLVM=1 LLVM_IAS=1
ALIOTH_KERNEL_515_REQUIRED_FILES := $(addprefix $(TARGET_KERNEL_CLANG_PATH)/bin/,clang ld.lld llvm-ar llvm-nm llvm-objcopy llvm-strip) $(TARGET_KERNEL_SOURCE)/Makefile $(TARGET_KERNEL_SOURCE)/arch/arm64/configs/vendor/xiaomi/sm8250-common.config $(TARGET_KERNEL_SOURCE)/arch/arm64/configs/vendor/xiaomi/alioth.config \
    $(addprefix kernel-research/alioth-5.15/sources/vendor/qcom/opensource/,audio-kernel/legacy/Makefile display-drivers/Makefile graphics-kernel/Makefile securemsm-kernel/Makefile mm-drivers/msm_ext_display/Makefile camera-kernel/Makefile video-driver/Makefile wlan/platform/Makefile wlan/qcacld-3.0/Makefile wlan/fw-api/fw/wmi_unified.h wlan/qca-wifi-host-cmn/os_if/linux/qca_vendor.h)
$(foreach file,$(ALIOTH_KERNEL_515_REQUIRED_FILES),$(if $(wildcard $(file)),,$(error Missing 5.15 build dependency $(file); sync kernel-5.15/manifest.xml)))
TARGET_KERNEL_EXT_MODULE_ROOT := $(ALIOTH_KERNEL_515_PATH)
TARGET_KERNEL_EXT_MODULES := external
BOARD_BOOT_HEADER_VERSION := 3
BOARD_KERNEL_IMAGE_NAME := Image
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_PREBUILT_DTBIMAGE_DIR :=
BOARD_PREBUILT_DTBOIMAGE := $(OUT_DIR)/target/product/$(TARGET_DEVICE)/obj/DTBO_OBJ/dtbo.img
BOARD_CUSTOM_DTBIMG_MK := $(ALIOTH_KERNEL_515_PATH)/dt-images.mk
BOARD_CUSTOM_DTBOIMG_MK := $(ALIOTH_KERNEL_515_PATH)/dt-images.mk
include $(ALIOTH_KERNEL_515_PATH)/modules.mk
endif
