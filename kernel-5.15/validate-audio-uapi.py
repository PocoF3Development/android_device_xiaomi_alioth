#!/usr/bin/env python3
"""Check the legacy/native compressed audio contract for both Android ABIs."""
from pathlib import Path
import argparse, json, re, subprocess, tempfile
parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
p = parser.parse_args().root.resolve(); r = p/'kernel-research/alioth-5.15'; k = r/'msm-kernel'
clang = p/'prebuilts/clang/host/linux-x86/clang-r563880c/bin/clang'
gen = p/'out/soong/.intermediates/vendor/lineage/build/soong/generated_kernel_includes/gen'
stage = Path(tempfile.mkdtemp(prefix='alioth-audio-uapi-'))
for mode, inc in [('core', k/'include/uapi'), ('driver', k/'include/uapi/audio')]:
    dest = stage/mode/'sound'; dest.mkdir(parents=True)
    for name in ['compress_params.h', 'compress_offload.h']:
        subprocess.run(['bash', str(k/'scripts/headers_install.sh'), str(inc/'sound'/name), str(dest/name)], cwd=gen, check=True)
source = """#include <linux/ioctl.h>
#include <sound/compress_offload.h>
const unsigned int uapi_layout[] = {sizeof(struct snd_codec), sizeof(union snd_codec_options), __builtin_offsetof(struct snd_codec, compr_passthr), __builtin_offsetof(struct snd_codec, flags), sizeof(struct snd_compr_params), sizeof(struct snd_compr_tstamp), sizeof(struct snd_compr_avail), sizeof(struct snd_codec_metadata), SNDRV_COMPRESS_SET_PARAMS, SNDRV_COMPRESS_TSTAMP, SNDRV_COMPRESS_AVAIL, SNDRV_COMPRESS_SET_NEXT_TRACK_PARAM, SND_AUDIOCODEC_ALAC, SND_AUDIOCODEC_APE};
"""
report = {}; resource = subprocess.check_output([str(clang), '-print-resource-dir'], text=True).strip()
for arch in ['aarch64-linux-android37', 'armv7a-linux-androideabi37']:
    layouts = {}
    for mode in ['core', 'driver']:
        cmd = [str(clang), '--target='+arch, '-nostdinc', '-S', '-x', 'c', '-', '-I'+str(stage/mode), '-I'+str(p/'bionic/libc/kernel/uapi'/('asm-arm64' if arch.startswith('aarch64') else 'asm-arm')), '-I'+str(p/'bionic/libc/kernel/uapi'), '-I'+str(p/'bionic/libc/kernel/uapi'), '-isystem'+resource+'/include', '-isystem'+str(p/'bionic/libc/include'), '-isystem'+str(p/'bionic/libc/kernel/android/uapi'), '-isystem'+str(p/'bionic/libc/kernel/uapi'), '-o', '-']
        result = subprocess.run(cmd, input=source, text=True, capture_output=True)
        if result.returncode:
            raise SystemExit(result.stderr)
        body = result.stdout.split('uapi_layout:')[1].split('.size')[0]
        layouts[mode] = [int(x) for x in re.findall(r'\.(?:word|long)\s+(\d+)', body)]
    assert layouts['core'] == layouts['driver'] and len(layouts['core']) == 14, layouts
    report[arch] = layouts['core']
assert report['aarch64-linux-android37'] == report['armv7a-linux-androideabi37'], report
(r/'compressed-audio-uapi-validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
