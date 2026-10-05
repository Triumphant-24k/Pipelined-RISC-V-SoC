# Transfer without Git on the server

Generate a materialized source archive on your laptop:

```powershell
.\scripts\run.ps1 -Target all
wsl -d Ubuntu-22.04 -- bash -lc 'cd "/mnt/c/Users/Trium/OneDrive/Desktop/IMP/Pipelined RISC-V SoC" && python3 scripts/package.py'
scp -i "$env:USERPROFILE\.ssh\cadence_ed25519" ".\build\pipelined-soc-source.tar.gz" 24bvd0168@cadence.vit.ac.in:~/
```

When SSH is reachable, extract into a new project directory on the server:

```bash
mkdir -p ~/projects
tar -xzf ~/pipelined-soc-source.tar.gz -C ~/projects
cd ~/projects/pipelined-soc
make all
```

The archive contains the dependency source files and licenses, but excludes
Git metadata and generated build files. Git is not required to build from it.
Required compiler/simulator tools still need to be installed or accessible in
your permitted server environment. Genus/Innovus flows additionally need the
college's authorized technology files and licenses. No remote upload or server
filesystem modification was performed during this task.

Extracting another archive into the same directory overwrites matching files.
Use a fresh destination for each revision, and download any server edits before
replacing files. Keep GitHub commits/pushes on your laptop.
