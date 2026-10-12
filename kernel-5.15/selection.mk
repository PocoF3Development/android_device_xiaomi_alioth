TARGET_USE_ALIOTH_KERNEL_515 ?= false
ifneq ($(words $(TARGET_USE_ALIOTH_KERNEL_515)),1)
$(error TARGET_USE_ALIOTH_KERNEL_515 must be exactly true or false)
endif
ifeq ($(filter true false,$(TARGET_USE_ALIOTH_KERNEL_515)),)
$(error TARGET_USE_ALIOTH_KERNEL_515 must be exactly true or false)
endif
