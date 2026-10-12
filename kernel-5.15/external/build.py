#!/usr/bin/env python3
"""Build dependency-ordered vendor drivers with Android's selected LLVM tools."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess
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
# Android mounts source directories read-only. Keep external Kbuild outputs
# under KERNEL_OBJ, preserving the vendor layout and cross-driver dependencies.
roots = ['mm-drivers', 'graphics-kernel', 'securemsm-kernel', 'display-drivers',
         'audio-kernel/legacy', 'wlan/platform', 'wlan/qcacld-3.0', 'wlan/fw-api',
         'wlan/qca-wifi-host-cmn', 'camera-kernel']
inventory = {}; revisions = {}; layout = hashlib.sha256()
for relative in roots:
    source = v / relative
    files = subprocess.check_output(['git', '-C', str(source), 'ls-files',
                                     '--cached', '--others', '--exclude-standard', '-z'])
    names = sorted(set(os.fsdecode(x) for x in files.split(b'\0') if x))
    names = [name for name in names
             if not name.endswith(('.o', '.ko', '.cmd', '.mod', '.mod.c', '.o.d', '.symversions'))
             and Path(name).name not in ('Module.symvers', 'modules.order')
             and '.tmp_versions' not in Path(name).parts]
    if relative == 'wlan/qcacld-3.0' and (source / 'cmn').is_symlink():
        names = sorted(set(names + ['cmn']))
    inventory[relative] = names
    revisions[relative] = subprocess.check_output(
        ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    for name in names:
        path = source / name
        if not path.exists():
            raise SystemExit('Missing vendor source: '+str(path))
        layout.update(os.fsencode(relative+'/'+name)+b'\0')
        if path.is_symlink(): layout.update(os.fsencode(os.readlink(path))+b'\0')
staged = o / 'external' / layout.hexdigest()[:16] / 'vendor/qcom/opensource'
content = hashlib.sha256()
for relative, names in inventory.items():
    for name in names:
        source = v / relative / name; dest = staged / relative / name
        assert dest.is_relative_to(staged), 'invalid source inventory path'
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target = os.readlink(source)
            if not dest.is_symlink():
                if dest.exists(): raise SystemExit('Staging path collision: '+str(dest))
                dest.symlink_to(target)
            elif os.readlink(dest) != target:
                raise SystemExit('Staging symlink differs: '+str(dest))
            payload = os.fsencode(target)
        else:
            payload = source.read_bytes()
            if not dest.is_file() or dest.read_bytes() != payload:
                shutil.copy2(source, dest)
        content.update(os.fsencode(relative+'/'+name)+b'\0'+hashlib.sha256(payload).digest())
(o / 'external-source-staging.json').write_text(json.dumps({
    'staged_root': str(staged), 'source_heads': revisions,
    'source_content_sha256': content.hexdigest(),
    'source_directories_read_only': True}, indent=2)+'\n')
v = staged

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
