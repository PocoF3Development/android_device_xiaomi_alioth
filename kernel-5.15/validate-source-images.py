#!/usr/bin/env python3
"""Verify Android-packaged source kernel images without accessing a device."""
import argparse, gzip, hashlib, json, shutil, struct, subprocess, tempfile
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--images', type=Path, help='Validate an extracted OTA image directory')
parser.add_argument('--report', type=Path, help='Write evidence separately from raw product images')
a = parser.parse_args(); root = a.root.resolve()
research = root/'kernel-research/alioth-5.15'
product = root/'out/target/product/alioth'
kernel = research/'msm-kernel'; obj = product/'obj/KERNEL_OBJ'
images = a.images.resolve() if a.images else product
stage = Path(tempfile.mkdtemp(prefix='alioth-source-images-'))
def run(args):
    return subprocess.check_output([str(x) for x in args], stderr=subprocess.STDOUT)
def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()
def cpio(data):
    entries = {}; pos = 0
    while pos < len(data):
        while pos < len(data) and data[pos] == 0: pos += 1
        if pos == len(data): break
        assert data[pos:pos+6] in (b'070701', b'070702'), 'unexpected ramdisk format'
        fields = [int(data[pos+6+i*8:pos+14+i*8], 16) for i in range(13)]
        size, namesize = fields[6], fields[11]; pos += 110
        name = data[pos:pos+namesize-1].decode(); pos = (pos+namesize+3)&~3
        payload = data[pos:pos+size]; assert len(payload) == size
        pos = (pos+size+3)&~3
        if name != 'TRAILER!!!': entries[name.removeprefix('./')] = payload
    return entries
for name in ('boot', 'vendor_boot'):
    run(['python3', root/'system/tools/mkbootimg/unpack_bootimg.py', '--boot_img', images/(name+'.img'), '--out', stage/name])
image = stage/'boot/kernel'
assert image.read_bytes() == (obj/'arch/arm64/boot/Image').read_bytes(), 'packaged kernel mismatch'
config = run(['bash', kernel/'scripts/extract-ikconfig', image])
assert config == (obj/'.config').read_bytes(), 'embedded configuration mismatch'
assert b'Linux/arm64 5.15.206' in config and b'clang version 21.0.0' in config
assert b'CONFIG_LTO_NONE=y\n' in config
assert b'CONFIG_SECURITY_SELINUX_FORCE_PERMISSIVE=y\n' in config
assert b'CONFIG_SECURITY_SELINUX_DEVELOP=y\n' in config
# Check the actual header arguments, rather than only the makefile.
vendor_header = (images/'vendor_boot.img').read_bytes()[:2112]
assert vendor_header[:8] == b'VNDRBOOT'
vendor_cmdline = vendor_header[28:2076].split(b'\0', 1)[0].decode().split()
assert [x for x in vendor_cmdline if x.startswith('androidboot.usbcontroller=')] == ['androidboot.usbcontroller=a600000.usb']
assert 'androidboot.selinux=permissive' in vendor_cmdline
assert 'enforcing=0' in vendor_cmdline
base = stage/'vendor_boot/dtb'
expected = stage/'expected.dtb'
shutil.copy2(obj/'arch/arm64/boot/dts/qcom/sm8250-xiaomi-alioth.dtb', expected)
run(['fdtput', '-t', 'x', expected, '/', 'qcom,board-id', '0', '0'])
assert base.read_bytes() == expected.read_bytes(), 'packaged source DTB mismatch'
table = (images/'dtbo.img').read_bytes(); header = struct.unpack('>8I', table[:32])
assert header[0] == 0xd7b7ab1e and header[4] == 1 and header[6] == 4096
entry = struct.unpack('>8I', table[header[5]:header[5]+32]); assert entry[2:4] == (0, 0)
overlay = stage/'overlay.dtbo'; overlay.write_bytes(table[entry[1]:entry[1]+entry[0]])
assert overlay.read_bytes() == (product/'obj/DTBO_OBJ/alioth.dtbo').read_bytes()
merged = stage/'merged.dtb'; run(['fdtoverlay', '-i', base, '-o', merged, overlay])
assert run(['fdtget', '-t', 'x', base, '/', 'qcom,board-id']).strip() == b'0 0'
assert run(['fdtget', '-t', 'x', merged, '/', 'qcom,board-id']).strip() == b'2c 0'
ramdisk = (stage/'vendor_boot/vendor_ramdisk').read_bytes()
if ramdisk.startswith(b'\x1f\x8b'): ramdisk = gzip.decompress(ramdisk)
elif not ramdisk.startswith((b'070701', b'070702')):
    ramdisk = subprocess.run(['lz4', '-dc'], input=ramdisk, check=True, capture_output=True).stdout
entries = cpio(ramdisk)
module_dir = product/'vendor_ramdisk/lib/modules'
expected_modules = (root/'device/xiaomi/alioth/kernel-5.15/modules.mk').read_text().split('BOARD_VENDOR_KERNEL_MODULES_LOAD := ')[1].splitlines()[0].split()
modules = sorted(module_dir.glob('*.ko'))
assert {path.name for path in modules} == set(expected_modules)
assert len(expected_modules) == len(set(expected_modules))
for path in module_dir.iterdir():
    if path.is_file(): assert entries['lib/modules/'+path.name] == path.read_bytes(), path.name
for name in ('boot.img', 'vendor_boot.img', 'dtbo.img'):
    run(['python3', root/'external/avb/avbtool.py', 'verify_image', '--image', images/name])
report = {'release': (obj/'include/config/kernel.release').read_text().strip(),
          'packaged_kernel_and_config_match': True, 'source_dtb_and_overlay_match': True,
          'overlay_merge_passed': True, 'vendor_ramdisk_modules': len(modules),
          'module_metadata_matches': True, 'avb_images_verified': True,
          'global_permissive_config_and_arguments': True,
          'native_usb_controller_argument': 'a600000.usb',
          'images': {n: {'bytes': (images/n).stat().st_size, 'sha256': digest(images/n)}
                     for n in ('boot.img', 'vendor_boot.img', 'dtbo.img')},
          'flashed': False, 'hardware_boot_verified': False}
(a.report or research/'android-source-image-validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
