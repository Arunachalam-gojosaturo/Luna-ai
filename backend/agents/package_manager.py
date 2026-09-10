import asyncio
import subprocess
import uuid
from backend.core.task_manager import task_manager

class PackageManagerAgent:
    def __init__(self):
        self.managers = ["pacman", "yay", "paru", "flatpak"]
        self.detected_managers = self._detect_managers()

    def _detect_managers(self) -> list:
        detected = []
        for pm in self.managers:
            try:
                # Check if the command exists
                res = subprocess.run(["which", pm], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode == 0:
                    detected.append(pm)
            except Exception:
                pass
        return detected

    async def run_command_live(self, cmd: list, task_id: str):
        await task_manager.update_progress(task_id, f"Running: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            await task_manager.update_progress(task_id, line.decode().strip())
            
        await process.wait()
        return process.returncode == 0

    async def search_package(self, package_name: str) -> str:
        results = []
        for pm in self.detected_managers:
            try:
                cmd = [pm, "-Ss", package_name] if pm in ["pacman", "yay", "paru"] else ["flatpak", "search", package_name]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                if stdout:
                    results.append(f"--- {pm} results ---\n{stdout.decode()[:500]}...\n")
            except Exception:
                pass
                
        if not results:
            return f"No results found for {package_name} in any package manager."
        return "\n".join(results)

    async def _install_task(self, package_name: str, task_id: str):
        await task_manager.update_progress(task_id, f"Resolving dependencies for {package_name}...")
        
        # We need user confirmation before proceeding with actual installation
        # For yay/pacman we usually add --noconfirm, but we want LUNA to confirm first.
        confirmed = await task_manager.request_confirmation(task_id, f"Are you sure you want to install '{package_name}'?")
        if not confirmed:
            raise Exception("Installation cancelled by user.")
            
        await task_manager.update_progress(task_id, "Downloading and installing...")
        
        success = False
        for pm in self.detected_managers:
            await task_manager.update_progress(task_id, f"Trying {pm}...")
            cmd = [pm, "-S", "--noconfirm", package_name] if pm in ["pacman", "yay", "paru"] else ["flatpak", "install", "-y", package_name]
            
            # Since this requires sudo for pacman, let's assume we use pkexec or the user runs LUNA as a service with rights.
            # For this prototype, we'll prefix sudo for pacman.
            if pm == "pacman":
                cmd = ["sudo", "-n"] + cmd  # -n for non-interactive sudo (fails if password required)
                
            if await self.run_command_live(cmd, task_id):
                success = True
                await task_manager.update_progress(task_id, f"Successfully installed {package_name} using {pm}.")
                break
                
        if not success:
            raise Exception(f"Failed to install {package_name} across all available package managers.")
            
        return f"Successfully installed {package_name}"

    async def install_package(self, package_name: str) -> str:
        task_id = f"pkg_install_{uuid.uuid4().hex[:8]}"
        # Start background task
        await task_manager.start_task(task_id, f"Install {package_name}", self._install_task(package_name, task_id))
        return f"Started installation task {task_id}. I will notify you when it requires confirmation or finishes."

    async def _remove_task(self, package_name: str, task_id: str):
        confirmed = await task_manager.request_confirmation(task_id, f"WARNING: Destructive action. Remove '{package_name}'?")
        if not confirmed:
            raise Exception("Removal cancelled by user.")
            
        success = False
        for pm in self.detected_managers:
            cmd = [pm, "-Rns", "--noconfirm", package_name] if pm in ["pacman", "yay", "paru"] else ["flatpak", "uninstall", "-y", package_name]
            if pm == "pacman":
                cmd = ["sudo", "-n"] + cmd
                
            if await self.run_command_live(cmd, task_id):
                success = True
                await task_manager.update_progress(task_id, f"Successfully removed {package_name}.")
                break
                
        if not success:
            raise Exception(f"Failed to remove {package_name}.")
        return f"Removed {package_name}"

    async def remove_package(self, package_name: str) -> str:
        task_id = f"pkg_remove_{uuid.uuid4().hex[:8]}"
        await task_manager.start_task(task_id, f"Remove {package_name}", self._remove_task(package_name, task_id))
        return f"Started removal task {task_id}. Awaiting your confirmation."

    async def execute(self, command: str = "", *args, **kwargs) -> dict:
        intent = command or (args[0] if args else "")
        words = intent.lower().split()
        
        # Package installation
        filler_words = {"the", "a", "an", "package", "app", "application", "for", "please"}
        if "install" in words:
            idx = words.index("install")
            target_idx = idx + 1
            while target_idx < len(words) and words[target_idx] in filler_words:
                target_idx += 1
            if target_idx < len(words):
                pkg = words[target_idx].strip("'\"")
                msg = await self.install_package(pkg)
                return {"status": "success", "action": "PACKAGE_MANAGER", "sysCommand": f"Install {pkg}", "msg": msg, "alreadyExecuted": True}
        elif "remove" in words or "uninstall" in words:
            idx = words.index("remove") if "remove" in words else words.index("uninstall")
            target_idx = idx + 1
            while target_idx < len(words) and words[target_idx] in filler_words:
                target_idx += 1
            if target_idx < len(words):
                pkg = words[target_idx].strip("'\"")
                msg = await self.remove_package(pkg)
                return {"status": "success", "action": "PACKAGE_MANAGER", "sysCommand": f"Remove {pkg}", "msg": msg, "alreadyExecuted": True}
        elif "search" in words:
            idx = words.index("search")
            target_idx = idx + 1
            while target_idx < len(words) and words[target_idx] in filler_words:
                target_idx += 1
            if target_idx < len(words):
                pkg = words[target_idx].strip("'\"")
                msg = await self.search_package(pkg)
                return {"status": "success", "action": "PACKAGE_MANAGER", "sysCommand": f"Search {pkg}", "msg": msg[:500], "alreadyExecuted": True}
        
        return {"status": "error", "action": "NONE", "stderr": "Could not understand package manager intent.", "alreadyExecuted": True}

    async def verify(self, execution_result: dict) -> bool:
        return execution_result.get("status") == "success" or execution_result.get("success", False)

package_manager_agent = PackageManagerAgent()
