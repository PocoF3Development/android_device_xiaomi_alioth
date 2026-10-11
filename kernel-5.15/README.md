# Experimental alioth 5.15 Android integration

Not production ready: the latest device tests did not boot Android. Camera/Xiaomi vendor ABI, RMNET and other donor parity gaps remain documented in the bringup repository. The current bundle is forced permissive and uses verbose panic diagnostics; do not ship it as a production kernel.

Build the kernel and eight external groups with the research configure/compile/stage scripts, then pack and independently validate the test images. Run `python3 kernel-research/alioth-5.15/export-android-kernel-bundle.py` from the workspace. This exports Image, wildcard base DTB, matching board overlay and all matching modules, not saved ramdisks. The exporter refuses a pre-existing bundle; preserve it under another name before exporting a new revision. Files under prebuilt are ignored by Git.

Use the existing `lineage_alioth-cp2a-user` lunch target for the default 5.15 profile. Set `TARGET_USE_ALIOTH_KERNEL_515=false` explicitly to build the donor 4.19 kernel. The BoardConfig profile requires the VAB/vendor_boot layout. Android builds fresh boot/vendor_boot ramdisks, module dependencies/load lists and AVB image metadata. This profile uses validated prebuilts; it does not make the existing Lineage in-tree kernel target compile the eight out-of-tree projects. Kernel and module source builds remain the research build workflow. Lineage's existing official-release prohibition on forced prebuilt kernels remains applicable.

No full ROM build or device boot is established by a Makefile parse. Do not claim production readiness until device boot, storage decryption and peripheral/vendor interfaces pass hardware tests.

Normal boot loads all matching modules; recovery and charger retain the first-stage subset. See the bringup repository ROM_COMPATIBILITY.md and legacy path inventory for outstanding vendor contracts.
