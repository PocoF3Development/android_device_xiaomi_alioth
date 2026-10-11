# SPDX-License-Identifier: GPL-2.0-only
.DEFAULT_GOAL := modules
.PHONY: modules modules_install
modules modules_install:
	+python3 $(CURDIR)/build.py --kernel $(KERNEL_SRC) --out $(abspath $(O)) --make "$(MAKE)" --target $@ --install "$(INSTALL_MOD_PATH)" --strip "$(INSTALL_MOD_STRIP)"
