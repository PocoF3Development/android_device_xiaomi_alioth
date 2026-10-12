# Alioth source-built 5.15 development profile

Development only; Android boot and full hardware functionality remain unverified.

The default profile builds Image, DTBs and all nine external driver groups from
source with checkout Android Clang r563880c (LLVM 21), LLVM integrated assembly,
and no LTO. No exported kernel/module prebuilt bundle is required. Android's
`generated_kernel_includes` runs native 5.15 `headers_install`; matching legacy
audio, graphics and display UAPI is exported by the kernel source and checked
against the active drivers. The donor buffer-sizing helpers are also exported.
Native and driver compressed-audio layouts/ioctl values are checked for both
Android ABIs with `validate-audio-uapi.py`.

Use the existing Evolution X checkout and build:

```sh
. build/envsetup.sh
lunch lineage_alioth-cp2a-user
m evolution
```

The external wrapper preserves dependency order: external display, graphics,
securemsm, display, audio, WLAN platform, WLAN, video, camera. It stages driver sources
under KERNEL_OBJ so Android can keep the checkout read-only; source revisions
and content hashes are recorded with the output. Depmod and required module
load lists must pass before packaging. Modules are packaged into both vendor and
vendor ramdisk; first-stage/recovery/charger load the 24 essential modules and
their dependencies, then vendor init loads the complete list after mounts.

DTB and DTBO are built from the same kernel output/configuration. The wildcard
base board selector and board-44 overlay preserve the current experimental
bootloader strategy. This does not establish a successful device boot.

`manifest.xml` records all 12 core/driver/header repositories and the integration
device/common branches. On a fresh checkout, use it as a local manifest after
reconciling any existing projects at those paths; do not overwrite existing local
work. Its copyfile installs the Kati research scan boundary. Existing Android
Clang and Android platform dependencies remain supplied by the ROM manifest.

Set `TARGET_USE_ALIOTH_KERNEL_515=false` before sourcing/lunch to explicitly use
the existing donor 4.19 source profile. Other values are rejected. The 5.15 profile
requires the alioth virtual-A/B vendor_boot layout, refuses missing dependencies,
and does not fall back to stale prebuilts. The temporary debug configuration
includes permissive SELinux; it is not intended for production.

After an Android source build, verify both the kernel/module outputs and the packaged images:

```sh
python3 device/xiaomi/alioth/kernel-5.15/validate-source-build.py --root "$PWD"
python3 device/xiaomi/alioth/kernel-5.15/validate-source-images.py --root "$PWD"
```

The image validator independently unpacks the boot images, compares the embedded kernel configuration and native DTB/overlay, verifies all 207 vendor-ramdisk modules and metadata, and checks AVB image signatures. These checks do not establish successful hardware boot.
