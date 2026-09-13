"""Create a complete source archive and checksum-pinned local Arch build recipe."""
from pathlib import Path
import hashlib
import tarfile
root=Path(__file__).resolve().parents[1]
dist=root/'dist';dist.mkdir(exist_ok=True)
name='whichwayisup-refresh-0.3.0'
archive=dist/(name+'.tar.gz')
def include(member):
    if '__pycache__' in Path(member.name).parts or member.name.endswith('.pyc'):return None
    member.uid=member.gid=0;member.uname=member.gname='root'
    return member
with tarfile.open(archive,'w:gz') as tar:
    for path in sorted(root.iterdir()):
        if path.name in ('.git','dist','.venv'):continue
        tar.add(path,arcname=name+'/'+path.name,filter=include)
checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
(dist/'PKGBUILD').write_text((root/'packaging/PKGBUILD.in').read_text().replace('@SHA256@',checksum))
(dist/'SHA256SUMS').write_text(checksum+'  '+archive.name+'\n')
print(archive)
print('Build Arch package: cd dist && makepkg')
