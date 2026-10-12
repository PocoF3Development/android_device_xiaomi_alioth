# Experimental development kernel; not production ready.
# Research dependencies contain duplicate Android.bp modules and are not ROM projects.
# Kbuild consumes these sources explicitly through the kernel task.
PRODUCT_SOURCE_ROOT_DIRS += -kernel-research
include device/xiaomi/alioth/kernel-5.15/selection.mk
ifeq ($(TARGET_USE_ALIOTH_KERNEL_515),true)
PRODUCT_PACKAGES += toolbox_vendor
PRODUCT_COPY_FILES += \
    device/xiaomi/alioth/kernel-5.15/init.alioth.modules.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.alioth.modules.rc
PRODUCT_COPY_FILES += \
    device/xiaomi/alioth/kernel-5.15/modules.load.recovery:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/lib/modules/modules.load.recovery \
    device/xiaomi/alioth/kernel-5.15/modules.load.charger:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/lib/modules/modules.load.charger
endif
