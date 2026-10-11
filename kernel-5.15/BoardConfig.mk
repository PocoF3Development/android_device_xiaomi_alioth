# Experimental alioth 5.15 integration; not production ready.
# Default for alioth; set TARGET_USE_ALIOTH_KERNEL_515=false for the donor kernel.
TARGET_USE_ALIOTH_KERNEL_515 ?= true
ifeq ($(TARGET_USE_ALIOTH_KERNEL_515),true)
ifneq ($(TARGET_IS_VAB),true)
$(error Alioth 5.15 profile requires the vendor_boot / VAB partition layout)
endif
ALIOTH_KERNEL_515_BUNDLE := device/xiaomi/alioth/kernel-5.15/prebuilt
ifeq ($(wildcard $(ALIOTH_KERNEL_515_BUNDLE)/modules.mk),)
$(error Run kernel-research/alioth-5.15/export-android-kernel-bundle.py first)
endif
TARGET_KERNEL_SOURCE := kernel-research/alioth-5.15/msm-kernel
TARGET_FORCE_PREBUILT_KERNEL := true
TARGET_PREBUILT_KERNEL := $(ALIOTH_KERNEL_515_BUNDLE)/Image
TARGET_KERNEL_CONFIG := gki_defconfig
TARGET_KERNEL_CLANG_VERSION := r450784e
TARGET_KERNEL_CLANG_PATH := $(abspath kernel-research/alioth-5.15/toolchain/clang-r450784e)
BOARD_BOOT_HEADER_VERSION := 3
BOARD_KERNEL_IMAGE_NAME := Image
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_PREBUILT_DTBIMAGE_DIR := $(ALIOTH_KERNEL_515_BUNDLE)/dtb
BOARD_PREBUILT_DTBOIMAGE := $(ALIOTH_KERNEL_515_BUNDLE)/dtbo.img
include $(ALIOTH_KERNEL_515_BUNDLE)/modules.mk
endif
