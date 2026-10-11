#!/bin/bash
# Yeni oturumda ROTAŞ çizim motorunu kurar (README'deki adımların otomatik hali)
set -e
R=/home/claude/rotas-cizim-motoru
mkdir -p /home/claude/nb /tmp/claude-0/xl /tmp/claude-0/p2/out /tmp/claude-0/ornek
cp -r $R/motor/. /home/claude/nb/
tar -xJf $R/kutuphane/ROTAS_2_MTY_BLOKLARI_2026-10-11.tar.xz -C /
tar -xJf $R/araclar/libredwg_yamali.tar.xz -C /
cp -r $R/araclar/dwgtools /home/claude/ && (cd /home/claude/dwgtools && gcc -O2 -o mkdwg mkdwg.c -I/usr/local/include -L/usr/local/lib -lredwg || true)
cp $R/sablon/ornek_yi.xlsx /tmp/claude-0/xl/
cp $R/araclar/*.py /tmp/claude-0/p2/
xz -dc $R/ornekler/new_block.dxf.xz > /tmp/claude-0/ornek/new_block.dxf
pip install --break-system-packages -q ezdxf shapely openpyxl pillow
# ACadSharp ile DWG yazıcı (AutoCAD 2018 / AC1032)
apt-get install -y -q dotnet-sdk-10.0 >/dev/null
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
[ -d /home/claude/domcr/acadsharp ] || GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/DomCR/acadsharp /home/claude/domcr/acadsharp
(cd /home/claude/domcr/acadsharp/src/ACadSharp && dotnet build -c Release -p:TargetFrameworks=net10.0 -p:GenerateDocumentationFile=false -p:GeneratePackageOnBuild=false --configfile $R/araclar/rotasdwg/nuget.config)
mkdir -p /home/claude/acad_build && cp -r $R/araclar/rotasdwg /home/claude/acad_build/ && cp $R/araclar/rotasdwg/nuget.config /home/claude/acad_build/
(cd /home/claude/acad_build/rotasdwg && dotnet build -c Release --configfile nuget.config)
echo "KURULUM TAMAM"
