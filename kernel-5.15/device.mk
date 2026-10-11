# Experimental development kernel; not production ready.
TARGET_USE_ALIOTH_KERNEL_515 ?= true
ifeq ($(TARGET_USE_ALIOTH_KERNEL_515),true)
PRODUCT_PACKAGES += toolbox_vendor
PRODUCT_COPY_FILES += \
    device/xiaomi/alioth/kernel-5.15/init.alioth.modules.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.alioth.modules.rc
endif
