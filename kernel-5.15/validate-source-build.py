#!/usr/bin/env python3
"""Validate Android-built core/module ABI and staged module load contracts."""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
a = parser.parse_args(); root = a.root.resolve()
profile = root / 'device/xiaomi/alioth/kernel-5.15'
research = root / 'kernel-research/alioth-5.15'
kernel = research / 'msm-kernel'
out = root / 'out/target/product/alioth/obj/KERNEL_OBJ'
product = root / 'out/target/product/alioth'
def run(args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()
def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()
config = (out / '.config').read_text()
assert 'CONFIG_LTO_NONE=y\n' in config
assert 'CONFIG_LTO_CLANG_THIN=y\n' not in config
assert 'CONFIG_LTO_CLANG_FULL=y\n' not in config
assert 'r563880c' in config and 'clang version 21.0.0' in config
image = out / 'arch/arm64/boot/Image'
embedded = subprocess.check_output(['bash', str(kernel / 'scripts/extract-ikconfig'), str(image)])
assert embedded == (out / '.config').read_bytes()
release = (out / 'include/config/kernel.release').read_text().strip()
head = run(['git', '-C', kernel, 'rev-parse', 'HEAD'])
assert head[:12] in release, (head, release)
module_config = (profile / 'modules.mk').read_text()
expected = module_config.split('BOARD_VENDOR_KERNEL_MODULES_LOAD := ')[1].splitlines()[0].split()
early = (profile / 'modules.load.early').read_text().split()
assert len(expected) == len(set(expected))
modules = {}
for partition in ['vendor', 'vendor_ramdisk']:
    directory = product / partition / 'lib/modules'
    files = {file.name: file for file in directory.glob('*.ko')}
    assert set(files) == set(expected), (partition, sorted(set(expected)-set(files)), sorted(set(files)-set(expected)))
    for name, file in files.items():
        assert run(['modinfo', '-F', 'vermagic', file]).split()[0] == release, name
    modules[partition] = {name: digest(file) for name, file in sorted(files.items())}
    load = (directory / 'modules.load').read_text().split()
    assert load == ([name.removesuffix('.ko') for name in expected] if partition == 'vendor' else early), (partition, load)
    if partition == 'vendor_ramdisk':
        for suffix in ['recovery', 'charger']:
            mode_load = (profile / ('modules.load.'+suffix)).read_text().split()
            assert (directory / ('modules.load.'+suffix)).read_text().split() == mode_load
            assert set(mode_load) <= {name.removesuffix('.ko') for name in expected}
            assert set(early + ['phy-msm-snps-hs', 'phy-msm-ssusb-qmp', 'dwc3-msm', 'qpnp-pdphy']) <= set(mode_load)
            if suffix == 'recovery':
                assert mode_load == [name.removesuffix('.ko') for name in expected]
assert modules['vendor'] == modules['vendor_ramdisk']
source_v = research / 'sources/vendor/qcom/opensource'
staging = json.loads((out / 'external-source-staging.json').read_text())
v = Path(staging['staged_root']).resolve()
assert v.is_relative_to(out / 'external')
for group, revision in staging['source_heads'].items():
    assert run(['git', '-C', source_v / group, 'rev-parse', 'HEAD']) == revision, group
groups = ['mm-drivers/msm_ext_display', 'graphics-kernel', 'securemsm-kernel', 'display-drivers', 'audio-kernel/legacy', 'wlan/platform', 'wlan/qcacld-3.0', 'camera-kernel', 'video-driver']
# Preserve a private diagnostic staging directory; never remove Android outputs.
stage = Path(tempfile.mkdtemp(prefix='alioth-source-abi-'))
moddir = stage / 'lib/modules' / release
moddir.mkdir(parents=True)
for file in (product / 'vendor/lib/modules').glob('*.ko'):
    (moddir / file.name).write_bytes(file.read_bytes())
for name in ['modules.builtin', 'modules.builtin.modinfo']:
    if (out / name).is_file():
        (moddir / name).write_bytes((out / name).read_bytes())
(moddir / 'modules.order').write_text(''.join(name+'\n' for name in expected))
symvers = stage / 'Module.symvers'
symvers.write_bytes((out / 'Module.symvers').read_bytes()+b''.join((v / group / 'Module.symvers').read_bytes() for group in groups))
result = subprocess.run(['depmod', '-e', '-E', str(symvers), '-b', str(stage), release], text=True, capture_output=True)
assert result.returncode == 0 and not result.stderr.strip(), result.stderr
report = {'kernel_head': head, 'release': release, 'compiler': next(line for line in config.splitlines() if line.startswith('CONFIG_CC_VERSION_TEXT=')), 'lto': 'none', 'image_sha256': digest(image), 'modules': len(expected), 'all_module_crcs_passed': True, 'partition_modules_identical': True, 'first_stage_modules': early, 'external_source_staging': staging, 'source_built': True, 'flashed': False, 'boot_validated': False, 'diagnostic_stage': str(stage)}
(research / 'android-source-build-validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
