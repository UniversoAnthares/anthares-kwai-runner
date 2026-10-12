#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def exe(name: str) -> str:
    value = shutil.which(name)
    if not value:
        raise RuntimeError(f"{name} not found")
    return value


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("output")
    args = p.parse_args()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    # Deliberately contains an immediate repetition, a false restart/filler, and
    # long silences. The clean continuation remains long enough for validation.
    chunks = [
        ("Hoje eu quero explicar como nasce uma boa história. Hoje eu quero explicar como nasce uma boa história.", 1.15),
        ("É... é... antes de continuar, eu preciso, eu preciso organizar a ideia. Eu preciso organizar a ideia com clareza.", 1.05),
        ("Uma cena funciona quando cada frase empurra a próxima frase e mantém o leitor dentro do movimento.", 0.90),
        ("Quando eu digo movimento, eu quero dizer movimento de pensamento, de imagem e de decisão.", 1.20),
        ("A parte que não ajuda esse fluxo precisa sair, porque o corte deve preservar apenas o que conduz a fala adiante.", 0.95),
        ("Por isso retiramos repetições, pausas vazias e vícios de linguagem sem cortar o sentido da explicação.", 1.00),
        ("O resultado final deve soar contínuo, natural e mais concentrado do que a gravação bruta.", 0.80),
    ]

    with tempfile.TemporaryDirectory(prefix="anthares-microcut-fixture-") as td:
        root = Path(td)
        inputs: list[Path] = []
        for idx, (text, silence) in enumerate(chunks):
            wav = root / f"speech-{idx:02d}.wav"
            subprocess.run([
                exe("espeak-ng"), "-v", "pt-br", "-s", "138", "-p", "46",
                "-w", str(wav), text,
            ], check=True, timeout=60)
            speech = root / f"speech-{idx:02d}.m4a"
            subprocess.run([
                exe("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(wav), "-ar", "48000", "-ac", "1", "-c:a", "aac", str(speech),
            ], check=True, timeout=60)
            inputs.append(speech)
            gap = root / f"gap-{idx:02d}.m4a"
            subprocess.run([
                exe("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{silence:.2f}",
                "-c:a", "aac", str(gap),
            ], check=True, timeout=60)
            inputs.append(gap)

        concat_file = root / "concat.txt"
        concat_file.write_text("\n".join(f"file '{x.as_posix()}'" for x in inputs) + "\n", encoding="utf-8")
        audio = root / "fixture.m4a"
        subprocess.run([
            exe("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(audio),
        ], check=True, timeout=120)

        subprocess.run([
            exe("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=0x111111:s=1280x720:r=30",
            "-i", str(audio), "-shortest", "-c:v", "libx264", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
            str(output),
        ], check=True, timeout=180)

    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
