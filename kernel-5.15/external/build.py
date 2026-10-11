#!/usr/bin/env python3
"""Build dependency-ordered vendor drivers with Android's selected LLVM tools."""
from pathlib import Path
import argparse, subprocess
parser = argparse.ArgumentParser()
parser.add_argument('--kernel', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--make', required=True)
parser.add_argument('--target', choices=['modules', 'modules_install'], required=True)
parser.add_argument('--install', default='')
parser.add_argument('--strip', default='')
a = parser.parse_args()
k = Path(a.kernel).resolve(); o = Path(a.out).resolve()
v = k.parent / 'sources/vendor/qcom/opensource'
for source, dest in [(v / 'audio-kernel/legacy/include/uapi/audio', k / 'include/uapi/audio'),
                     (v / 'graphics-kernel/include/uapi', k / 'include/uapi'),
                     (v / 'display-drivers/include/uapi/display', k / 'include/uapi')]:
    for header in source.rglob('*.h'):
        exported = dest / header.relative_to(source)
        if not exported.is_file() or exported.read_bytes() != header.read_bytes():
            raise SystemExit('UAPI export differs from driver: '+str(header))
base = [a.make, '-C', str(k), 'O='+str(o), 'ARCH=arm64', 'LLVM=1', 'LLVM_IAS=1', '-j8']
entries=[('ext-display',v/'mm-drivers/msm_ext_display',['MM_ROOT='+str(v/'mm-drivers'),'KERNEL_SRC='+str(k)]),('graphics',v/'graphics-kernel',['CONFIG_ARCH_KONA=y','KERNEL_SRC='+str(k),'KGSL_PATH='+str(v/'graphics-kernel')]),('securemsm',v/'securemsm-kernel',['CONFIG_ARCH_KONA=y','KERNEL_SRC='+str(k),'SSG_MODULE_ROOT='+str(v/'securemsm-kernel')]),('display',v/'display-drivers',['CONFIG_ARCH_KONA=y','CONFIG_DRM_MSM=m','KERNEL_SRC='+str(k),'KERNEL_ROOT='+str(k),'DISPLAY_ROOT='+str(v/'display-drivers')]),('audio',v/'audio-kernel/legacy',['MODNAME=audio','CONFIG_ARCH_KONA=y','KERNEL_SRC='+str(k),'AUDIO_ROOT='+str(v/'audio-kernel/legacy'),'LEGACY_PATH='+str(v/'audio-kernel/legacy')])]
entries += [
 ('wlan-platform', v/'wlan/platform', ['WLAN_PLATFORM_ROOT='+str(v/'wlan/platform'), 'CONFIG_CNSS_OUT_OF_TREE=y', 'CONFIG_CNSS2=m', 'CONFIG_CNSS2_QMI=y', 'CONFIG_CNSS_UTILS=m', 'CONFIG_CNSS_QMI_SVC=m', 'CONFIG_CNSS_PLAT_IPC_QMI_SVC=m', 'CONFIG_CNSS_GENL=m', 'CONFIG_WCNSS_MEM_PRE_ALLOC=m']),
 ('wlan', v/'wlan/qcacld-3.0', ['CONFIG_QCA_CLD_WLAN=m', 'CONFIG_QCA_CLD_WLAN_PROFILE=qca6390', 'CONFIG_CNSS2=m', 'CONFIG_CNSS_OUT_OF_TREE=y', 'MODNAME=wlan', 'WLAN_ROOT='+str(v/'wlan/qcacld-3.0'), 'WLAN_PLATFORM_INC='+str(v/'wlan/platform/inc')]),
 ('camera', v/'camera-kernel', ['CONFIG_ARCH_KONA=y', 'CAMERA_KERNEL_ROOT='+str(v/'camera-kernel'), 'KERNEL_ROOT='+str(k), 'MODNAME=camera']),
]
for name, root, flags in entries:
    if not (root / 'Makefile').is_file():
        raise SystemExit('Missing kernel dependency: '+str(root))
    symbols = []
    if name in ('display', 'audio'):
        symbols.append(v / 'mm-drivers/msm_ext_display/Module.symvers')
    if name in ('display', 'camera'):
        symbols.append(v / 'securemsm-kernel/Module.symvers')
    if name == 'wlan':
        symbols.append(v / 'wlan/platform/Module.symvers')
    if symbols:
        for symbol in symbols:
            if not symbol.is_file():
                raise SystemExit('Missing dependency symbols: '+str(symbol))
        flags.append('KBUILD_EXTRA_SYMBOLS='+' '.join(map(str, symbols)))
    if a.target == 'modules_install':
        flags += ['INSTALL_MOD_PATH='+a.install, 'INSTALL_MOD_STRIP='+a.strip]
    print('Alioth external driver: '+name+' '+a.target, flush=True)
    subprocess.run(base+['M='+str(root)]+flags+[a.target], check=True)
