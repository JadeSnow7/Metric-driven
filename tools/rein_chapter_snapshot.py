#!/usr/bin/env python3
"""Create a portable, independently recoverable chapter snapshot."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, tarfile, tempfile
from pathlib import Path

SKIP_DIRS = {'.git', 'node_modules', 'target', '.cargo-target', 'build', 'dist', 'deps'}
ROOT_AUX_DIRS = {'task-inputs', 'chapter-snapshots', 'evidence', 'experiments', 'work', 'snapshots'}
SKIP_FILES = {'.env'}

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

def manifest(root: Path) -> list[dict]:
    rows=[]
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        rel_dir = Path(current).relative_to(root)
        dirs[:] = [d for d in sorted(dirs) if not _skip_dir(d, rel_dir)]
        files = sorted(files)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.env.')]
        for name in list(dirs):
            p=Path(current)/name
            if p.is_symlink():
                dirs.remove(name); rel=p.relative_to(root).as_posix(); target=os.readlink(p)
                if not p.resolve().is_relative_to(root.resolve()): raise RuntimeError(f'symlink escapes source: {rel}')
                mode=p.lstat().st_mode & 0o777; rows.append({'path':rel,'symlink':target,'mode':mode,'git_exec':bool(mode & 0o111)})
        for name in files:
            if name in SKIP_FILES or (name.startswith('.env.') and name != '.env.example'): continue
            p=Path(current)/name; rel=p.relative_to(root).as_posix()
            if p.is_symlink():
                if not p.resolve().is_relative_to(root.resolve()): raise RuntimeError(f'symlink escapes source: {rel}')
                mode=p.lstat().st_mode & 0o777; rows.append({'path':rel,'symlink':os.readlink(p),'mode':mode,'git_exec':bool(mode & 0o111)})
            else:
                mode=p.stat().st_mode & 0o777; rows.append({'path':rel,'sha256':digest(p),'mode':mode,'git_exec':bool(mode & 0o111)})
    return sorted(rows,key=lambda x:x['path'])

def _skip_dir(name: str, parent: Path) -> bool:
    return name in SKIP_DIRS or (not parent.parts and name in ROOT_AUX_DIRS) or (name == 'cache' and parent.parts[-1:] == ('.vitepress',)) or name.startswith('.env.')

def copy_filtered(src: Path, dst: Path) -> None:
    if dst.exists(): raise RuntimeError(f'refusing overwrite: {dst}')
    dst.mkdir(parents=True)
    for current, dirs, files in os.walk(src, topdown=True, followlinks=False):
        rel=Path(current).relative_to(src); target_dir=dst/rel; target_dir.mkdir(parents=True,exist_ok=True)
        dirs[:] = sorted(dirs)
        for name in list(dirs):
            p=Path(current)/name
            if _skip_dir(name, rel):
                dirs.remove(name); continue
            if p.is_symlink():
                dirs.remove(name)
                if not p.resolve().is_relative_to(src.resolve()): raise RuntimeError(f'symlink escapes source: {p.relative_to(src)}')
                (target_dir/name).symlink_to(os.readlink(p))
        for name in sorted(files):
            if name in SKIP_FILES or (name.startswith('.env.') and name != '.env.example'): continue
            p=Path(current)/name
            if p.is_symlink():
                if not p.resolve().is_relative_to(src.resolve()): raise RuntimeError(f'symlink escapes source: {p.relative_to(src)}')
                (target_dir/name).symlink_to(os.readlink(p))
            else: shutil.copy2(p,target_dir/name)

def git_patch(base: Path, result: Path, patch_path: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); repo=td/'repo'; shutil.copytree(base,repo,symlinks=True); subprocess.run(['git','-C',str(repo),'init','-q'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(repo),'add','-A'],check=True,capture_output=True); base_tree=subprocess.check_output(['git','-C',str(repo),'write-tree'],text=True).strip()
        for child in repo.iterdir():
            if child.name=='.git': continue
            if child.is_dir() and not child.is_symlink(): shutil.rmtree(child)
            else: child.unlink()
        for child in result.iterdir():
            dest=repo/child.name
            if child.is_dir() and not child.is_symlink(): shutil.copytree(child,dest,symlinks=True)
            elif child.is_symlink(): dest.symlink_to(os.readlink(child))
            else: shutil.copy2(child,dest)
        subprocess.run(['git','-C',str(repo),'add','-A'],check=True,capture_output=True); result_tree=subprocess.check_output(['git','-C',str(repo),'write-tree'],text=True).strip()
        patch=subprocess.check_output(['git','-C',str(repo),'diff','--binary',base_tree,result_tree],text=True); patch_path.write_text(patch)

def make_tar(files: Path, root_name: str, destination: Path) -> None:
    with tarfile.open(destination,'w:gz') as tar: tar.add(files,arcname=root_name,recursive=True)

def snapshot(source: Path, chapter: str, output: Path, baseline: Path|None=None, portable_output: Path|None=None) -> Path:
    source=source.resolve(); output=output.resolve(); chapter=str(chapter)
    if not (chapter == 'pre-ch05' or (len(chapter) == 2 and chapter.isdigit())): raise RuntimeError('chapter must be two digits or pre-ch05')
    root_name = f'rein-{chapter}' if chapter.startswith('pre-') else f'rein-ch{chapter}'
    if not source.is_dir(): raise RuntimeError('source is not a directory')
    if output.exists(): raise RuntimeError(f'refusing overwrite: {output}')
    if output.is_relative_to(source): raise RuntimeError('output must not be inside source')
    if baseline and not baseline.is_dir(): raise RuntimeError('baseline is not a directory')
    output.mkdir(parents=True)
    files=output/'files'; copy_filtered(source,files)
    current_manifest=manifest(files); (output/'manifest.json').write_text(json.dumps({'chapter':root_name,'files':current_manifest},ensure_ascii=False,indent=2)+'\n')
    tar_path=output/f'{root_name}.tar.gz'; make_tar(files,root_name,tar_path)
    with tempfile.TemporaryDirectory() as td:
        tar_recovered=Path(td)/'tar-recovered'; tar_recovered.mkdir()
        with tarfile.open(tar_path) as archive: archive.extractall(tar_recovered)
        if _portable_manifest(tar_recovered/root_name)!=_portable_manifest(files): raise RuntimeError('tar recovery manifest mismatch')
        recovered=Path(td)/'recovered';
        if baseline:
            base=Path(td)/'base'; copy_filtered(baseline.resolve(),base); patch_path=output/'baseline.patch'; git_patch(base,files,patch_path)
            copy_filtered(base,recovered)
            recovered_check = recovered
            if patch_path.read_bytes():
                repo=Path(td)/'apply'; shutil.copytree(recovered,repo,symlinks=True); subprocess.run(['git','-C',str(repo),'init','-q'],check=True,capture_output=True)
                applied=subprocess.run(['git','-C',str(repo),'apply','--binary',str(patch_path)],capture_output=True)
                if applied.returncode: raise RuntimeError('baseline Git patch failed to apply')
                recovered_check = repo
            if _portable_manifest(recovered_check)!=_portable_manifest(files): raise RuntimeError('baseline recovery manifest mismatch')
        else:
            copy_filtered(files,recovered)
            if manifest(recovered)!=current_manifest: raise RuntimeError('snapshot recovery manifest mismatch')
    if portable_output:
        portable_output=portable_output.resolve()
        if portable_output.exists(): raise RuntimeError(f'refusing overwrite: {portable_output}')
        portable_output.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(tar_path,portable_output)
    return output

def _portable_manifest(root: Path) -> list[dict]:
    return [{k: row[k] for k in ('path','sha256','symlink','git_exec') if k in row} for row in manifest(root)]

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True); p.add_argument('--chapter',required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--baseline',type=Path); p.add_argument('--portable-output',type=Path); a=p.parse_args()
    try: snapshot(a.source,a.chapter,a.output,a.baseline,a.portable_output); return 0
    except (OSError,RuntimeError,subprocess.SubprocessError) as e: print(f'rein_chapter_snapshot: error: {e}',file=__import__('sys').stderr); return 2
if __name__=='__main__': raise SystemExit(main())
