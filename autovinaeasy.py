import customtkinter as ctk
from tkinter import filedialog
import os
import subprocess
import threading
import json
import csv
import re
import shutil
from pathlib import Path
from collections import Counter
from math import sqrt
from PIL import Image, ImageDraw, ImageFont

# Set tema dan warna
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VirtualScreeningApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoVinaEasy - Yaqin 2026")
        self.geometry("900x750")
        self.minsize(800, 950)

        # Variabel
        self.protein_path = ""
        self.ligand_folder = ""
        self.output_folder = ""
        self.vina_path = self.load_setting("vina_path", "vina")
        self.obabel_path = self.load_setting("obabel_path", "obabel")
        self.config_path = ""

        self.stop_flag = False
        self.top_only_var = ctk.BooleanVar(value=False)
        self.prepare_ligands_var = ctk.BooleanVar(value=True)
        self.latest_run_dir = None

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)
        self.grid_rowconfigure(7, weight=1) 
        # HEADER
        self.header_label = ctk.CTkLabel(self, text="AutoVinaEasy Pipeline", font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")
        
        # INPUT PROTEIN
        self.protein_label = ctk.CTkLabel(self, text="Protein File (PDB):")
        self.protein_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        self.protein_entry = ctk.CTkEntry(self, placeholder_text="Belum pilih file...", width=500)
        self.protein_entry.grid(row=1, column=1, padx=(0, 10), pady=10, sticky="ew")
        
        self.protein_btn = ctk.CTkButton(self, text="Browse", width=100, command=self.browse_protein)
        self.protein_btn.grid(row=1, column=2, padx=(0, 20), pady=10)

        # INPUT LIGAND
        self.ligand_label = ctk.CTkLabel(self, text="Ligand Folder (any format):")
        self.ligand_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        
        self.ligand_entry = ctk.CTkEntry(self, placeholder_text="Belum pilih folder...", width=500)
        self.ligand_entry.grid(row=2, column=1, padx=(0, 10), pady=10, sticky="ew")
        
        self.ligand_btn = ctk.CTkButton(self, text="Browse", width=100, command=self.browse_ligands)
        self.ligand_btn.grid(row=2, column=2, padx=(0, 20), pady=10)

        # INPUT OUTPUT FOLDER
        self.output_label = ctk.CTkLabel(self, text="Output Folder:")
        self.output_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        self.output_entry = ctk.CTkEntry(self, placeholder_text="Belum pilih folder...", width=500)
        self.output_entry.grid(row=3, column=1, padx=(0, 10), pady=10, sticky="ew")
        
        self.output_btn = ctk.CTkButton(self, text="Browse", width=100, command=self.browse_output)
        self.output_btn.grid(row=3, column=2, padx=(0, 20), pady=10)

        # OPTIONS FRAME
        self.option_frame = ctk.CTkFrame(self)
        self.option_frame.grid(row=4, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        self.option_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.auto_box_var = ctk.BooleanVar(value=True)
        self.auto_box_switch = ctk.CTkSwitch(self.option_frame, text="Auto Grid Box (Blind Docking)", 
                                            variable=self.auto_box_var, command=self.toggle_config_browse)
        self.auto_box_switch.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        # Config browse
        self.config_frame = ctk.CTkFrame(self.option_frame)
        self.clean_h_var = ctk.BooleanVar(value=True)
        self.clean_h_switch = ctk.CTkSwitch(self.option_frame, text="Auto Add H & Fix Bonds", variable=self.clean_h_var)
        self.clean_h_switch.grid(row=0, column=1, padx=20, pady=12, sticky="w")

        self.prepare_switch = ctk.CTkSwitch(self.option_frame, text="Prepare Ligands (PDBQT)", 
                                            variable=self.prepare_ligands_var)
        self.prepare_switch.grid(row=0, column=2, padx=20, pady=12, sticky="w")

        self.top_only_switch = ctk.CTkSwitch(self.option_frame, text="Hotspot from Top Ligands Only", 
                                            variable=self.top_only_var)
        self.top_only_switch.grid(row=0, column=3, padx=20, pady=12, sticky="w")

        self.exhaust_var = ctk.StringVar(value="32")
        self.exhaust_label = ctk.CTkLabel(self.option_frame, text="Exhaustiveness:")
        self.exhaust_label.grid(row=1, column=0, padx=(20, 10), pady=12, sticky="w")
        self.exhaust_combo = ctk.CTkComboBox(self.option_frame, values=["8", "16", "32", "64", "128"], 
                                            variable=self.exhaust_var, width=100)
        self.exhaust_combo.grid(row=1, column=0, padx=(100, 20), pady=12, sticky="w")

        # RUN & STOP BUTTON
        self.run_frame = ctk.CTkFrame(self)
        self.run_frame.grid(row=5, column=0, columnspan=3, padx=20, pady=20, sticky="ew")
        self.run_frame.grid_columnconfigure(0, weight=1)

        self.run_button = ctk.CTkButton(self.run_frame, text="START SCREENING", height=45, 
                                        font=ctk.CTkFont(size=16, weight="bold"),
                                        fg_color="#2caf50", hover_color="#228b3c", 
                                        command=self.start_screening_thread)
        self.run_button.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.stop_button = ctk.CTkButton(self.run_frame, text="STOP", height=45, 
                                        font=ctk.CTkFont(size=16, weight="bold"),
                                        fg_color="#d9534f", hover_color="#c9302c", 
                                        command=self.stop_screening, state="disabled")
        self.stop_button.pack(side="left", padx=10)

        # PROGRESS
        self.prog_label = ctk.CTkLabel(self, text="Progress: Ready")
        self.prog_label.grid(row=6, column=0, padx=20, pady=(10,0), sticky="w")
        
        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.grid(row=6, column=1, columnspan=2, padx=(0, 20), pady=(5,5), sticky="ew")
        self.progressbar.set(0)

        # LOG AREA
        self.log_textbox = ctk.CTkTextbox(self)
        self.log_textbox.grid(row=7, column=0, columnspan=3, padx=20, pady=(0, 5), sticky="nsew")
        self.log_textbox.insert("0.0", "System Ready...\nMenunggu input protein dan folder ligan.\n\n")

        # SETTINGS VINA & OBABEL 
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid(row=8, column=0, columnspan=3, padx=20, pady=(0, 5), sticky="ew")
        
        self.settings_btn = ctk.CTkButton(self.settings_frame, text="Settings (Vina & OBabel Location)", width=250, 
                                          fg_color="transparent", border_width=1, command=self.toggle_settings)
        self.settings_btn.pack(side="left", padx=10, pady=5)

        self.settings_content = ctk.CTkFrame(self.settings_frame)
        self.settings_visible = False

        # Vina setting
        self.vina_label = ctk.CTkLabel(self.settings_content, text="Vina Path:")
        self.vina_label.pack(side="top", padx=10, pady=(5,0), anchor="w")
        self.vina_entry = ctk.CTkEntry(self.settings_content, 
                                      placeholder_text="Path ke vina.exe atau 'vina' jika di PATH", 
                                      width=500)
        self.vina_entry.pack(side="top", padx=10, pady=(0,5), fill="x")
        self.vina_entry.insert(0, self.vina_path)
        self.vina_browse_btn = ctk.CTkButton(self.settings_content, text="Browse Vina", width=120, 
                                            command=self.browse_vina)
        self.vina_browse_btn.pack(side="top", padx=10, pady=5, anchor="w")

        # OBabel setting
        self.obabel_label = ctk.CTkLabel(self.settings_content, text="OBabel Path:")
        self.obabel_label.pack(side="top", padx=10, pady=(5,0), anchor="w")
        self.obabel_entry = ctk.CTkEntry(self.settings_content, 
                                        placeholder_text="Path ke obabel.exe atau 'obabel' jika di PATH", 
                                        width=500)
        self.obabel_entry.pack(side="top", padx=10, pady=(0,5), fill="x")
        self.obabel_entry.insert(0, self.obabel_path)
        self.obabel_browse_btn = ctk.CTkButton(self.settings_content, text="Browse OBabel", width=120, 
                                              command=self.browse_obabel)
        self.obabel_browse_btn.pack(side="top", padx=10, pady=5, anchor="w")

        self.settings_save_btn = ctk.CTkButton(self.settings_content, text="Save Settings", width=150, 
                                              fg_color="#1f6aa5", command=self.save_settings)
        self.settings_save_btn.pack(side="top", padx=10, pady=5, anchor="w")

        # OPEN OUTPUT FOLDER
        self.open_folder_btn = ctk.CTkButton(self, text="Open Latest Output Folder", 
                                            command=self.open_latest_folder, state="disabled")
        self.open_folder_btn.grid(row=9, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="ew")

    def log(self, message):
        """Menambahkan pesan ke log textbox"""
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.update_idletasks()

    def load_setting(self, key, default):
        """Load setting dari json"""
        settings_file = Path("vina_settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get(key, default)
            except:
                return default
        return default

    def save_settings(self):
        self.vina_path = self.vina_entry.get().strip()
        self.obabel_path = self.obabel_entry.get().strip()
        settings_file = Path("vina_settings.json")
        try:
            with open(settings_file, 'w') as f:
                json.dump({
                    "vina_path": self.vina_path,
                    "obabel_path": self.obabel_path
                }, f)
            self.log(f"Settings disimpan: Vina={self.vina_path}, OBabel={self.obabel_path}")
        except Exception as e:
            self.log(f"Error menyimpan settings: {e}")
        self.toggle_settings()

    def open_latest_folder(self):
        if self.latest_run_dir and self.latest_run_dir.exists():
            try:
                os.startfile(str(self.latest_run_dir))
            except:
                import platform
                system = platform.system()
                if system == "Windows":
                    os.startfile(str(self.latest_run_dir))
                elif system == "Darwin":
                    subprocess.run(["open", str(self.latest_run_dir)])
                else:
                    subprocess.run(["xdg-open", str(self.latest_run_dir)])

    def toggle_settings(self):
        if self.settings_visible:
            self.settings_content.pack_forget()
            self.settings_btn.configure(text="Settings (Vina & OBabel Location)")
            self.settings_visible = False
        else:
            self.settings_content.pack(side="left", fill="x", expand=True, pady=5)
            self.settings_btn.configure(text="Hide Settings")
            self.settings_visible = True

    def browse_vina(self):
        file = filedialog.askopenfilename(title="Pilih vina.exe", 
                                         filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if file:
            self.vina_entry.delete(0, "end")
            self.vina_entry.insert(0, file)

    def browse_obabel(self):
        file = filedialog.askopenfilename(title="Pilih obabel.exe", 
                                         filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if file:
            self.obabel_entry.delete(0, "end")
            self.obabel_entry.insert(0, file)

    def toggle_config_browse(self):
        if not self.auto_box_var.get():
            if not hasattr(self, 'config_entry'):
                self.config_entry = ctk.CTkEntry(self.config_frame, placeholder_text="Config file (.txt)...", width=300)
                self.config_entry.pack(side="left", padx=5)
                self.config_btn = ctk.CTkButton(self.config_frame, text="Browse Config", width=120, 
                                               command=self.browse_config)
                self.config_btn.pack(side="left", padx=5)
            
            self.config_frame.grid(row=2, column=0, columnspan=4, padx=20, pady=10, sticky="ew")
        else:
            self.config_frame.grid_forget()
            self.config_path = ""

    def browse_config(self):
        file = filedialog.askopenfilename(title="Pilih Config File", 
                                         filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file:
            self.config_path = file
            if hasattr(self, 'config_entry'):
                self.config_entry.delete(0, 'end')
                self.config_entry.insert(0, file)
            self.log(f"Config dimuat: {os.path.basename(file)}")

    def browse_protein(self):
        file = filedialog.askopenfilename(filetypes=[("PDB files", "*.pdb"), ("All files", "*.*")])
        if file:
            self.protein_path = file
            self.protein_entry.delete(0, 'end')
            self.protein_entry.insert(0, file)
            self.log(f"Protein dimuat: {os.path.basename(file)}")

    def browse_ligands(self):
        folder = filedialog.askdirectory(title="Pilih Folder Ligand")
        if folder:
            self.ligand_folder = folder
            self.ligand_entry.delete(0, 'end')
            self.ligand_entry.insert(0, folder)
            files = [p for p in Path(folder).rglob("*") if p.is_file()]
            self.log(f"Folder ligan: {folder} ({len(files)} file ditemukan)")

    def browse_output(self):
        folder = filedialog.askdirectory(title="Pilih Output Folder")
        if folder:
            self.output_folder = folder
            self.output_entry.delete(0, 'end')
            self.output_entry.insert(0, folder)
            self.log(f"Output folder: {folder}")

    def start_screening_thread(self):
        if not self.protein_path or not self.ligand_folder or not self.output_folder:
            self.log("Error: Pilih protein, folder ligan, dan output folder dulu!")
            return
        
        self.stop_flag = False
        threading.Thread(target=self.run_pipeline, daemon=True).start()
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def stop_screening(self):
        self.stop_flag = True
        self.log("Menghentikan proses...")
        self.stop_button.configure(state="disabled")

    def run_pipeline(self):
        self.log("Memulai virtual screening...\n")
        self.progressbar.set(0)

        protein_name = Path(self.protein_path).stem
        run_dir = Path(self.output_folder) / f"vina_screening_{protein_name}"
        run_dir.mkdir(parents=True, exist_ok=True)
        self.latest_run_dir = run_dir

        protein_pdbqt = run_dir / f"{protein_name}.pdbqt"
        ligands_pdbqt_dir = run_dir / "ligands_pdbqt"
        ligands_pdbqt_dir.mkdir(exist_ok=True)
        output_dir = run_dir / "output"
        output_dir.mkdir(exist_ok=True)
        complexes_dir = run_dir / "complexes"
        complexes_dir.mkdir(exist_ok=True)
        images_dir = run_dir / "interaction_images"
        images_dir.mkdir(exist_ok=True)

        # Prepare protein
        self.log("Preparing protein...")
        cmd_prep_prot = [
            self.obabel_path, "-ipdb", self.protein_path,
            "-opdbqt", "-O", str(protein_pdbqt),
            "-xr"
        ]
        if self.clean_h_var.get():
            cmd_prep_prot.append("-h")

        try:
            result = subprocess.run(cmd_prep_prot, check=True, capture_output=True, text=True)
            self.log("Protein siap")
        except subprocess.CalledProcessError as e:
            self.log(f"Gagal prepare protein: {e.stderr}")
            self.finish_run()
            return
        except Exception as e:
            self.log(f"Gagal prepare protein: {str(e)}")
            self.finish_run()
            return

        # Calculate protein dimensions for base box
        protein_dims = self.calculate_protein_dimensions(self.protein_path)

        # Prepare ligands atau gunakan yang sudah ada
        if self.prepare_ligands_var.get():
            self.log("Preparing ligands...")
            ligand_files = [p for p in Path(self.ligand_folder).rglob("*") if p.is_file()]
            total_ligands = len(ligand_files)
            if total_ligands == 0:
                self.log("Tidak ada file ligan ditemukan")
                self.finish_run()
                return

            error_log = run_dir / f"{protein_name}_preparation_errors.txt"
            skipped_ligands = []
            successful_prep = 0

            for i, lig_file in enumerate(ligand_files):
                if self.stop_flag:
                    self.log("Proses dihentikan user")
                    self.finish_run()
                    return

                out_file = ligands_pdbqt_dir / f"{lig_file.stem}.pdbqt"
                cmd = [self.obabel_path, str(lig_file), "-opdbqt", "-O", str(out_file), 
                      "--gen3d", "-h", "--partialcharge", "gasteiger"]

                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    if result.returncode == 0 and out_file.exists() and out_file.stat().st_size > 0:
                        successful_prep += 1
                    else:
                        msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                        skipped_ligands.append(f"{lig_file.name}: {msg[:200]}")
                        self.log(f"Skip prepare {lig_file.name}")
                except subprocess.TimeoutExpired:
                    skipped_ligands.append(f"{lig_file.name}: Timeout")
                    self.log(f"Timeout prepare {lig_file.name}")
                except Exception as e:
                    skipped_ligands.append(f"{lig_file.name}: {str(e)}")
                    self.log(f"Skip prepare {lig_file.name}")

                self.progressbar.set((i+1) / total_ligands * 0.2)

            if skipped_ligands:
                with open(error_log, 'w') as f:
                    f.write("Ligand preparation errors:\n\n")
                    f.write("\n".join(skipped_ligands))
                self.log(f"{len(skipped_ligands)} ligand gagal prepare -> lihat {error_log.name}")

            self.log(f"Prepare selesai: {successful_prep}/{total_ligands} ligand berhasil")
        else:
            self.log("Menggunakan data ligands yang sudah diolah...")
            ligand_files = list(Path(self.ligand_folder).glob("*.pdbqt"))
            total_ligands = len(ligand_files)
            if total_ligands == 0:
                self.log("Tidak ada file .pdbqt ditemukan di folder")
                self.finish_run()
                return
            
            for lig_file in ligand_files:
                target_file = ligands_pdbqt_dir / lig_file.name
                shutil.copy(lig_file, target_file)
            
            self.log(f"{total_ligands} file .pdbqt disalin ke folder kerja")

        # Grid box base
        self.log("Menghitung base grid box...")
        grid_info = {}
        if self.auto_box_var.get():
            center_x, center_y, center_z = protein_dims["center"]
            base_size_x, base_size_y, base_size_z = protein_dims["size"]
            grid_info = {
                "center": [center_x, center_y, center_z],
                "base_size": [base_size_x, base_size_y, base_size_z],
                "mode": "auto-blind-per-ligand"
            }
            self.log(f"Base auto grid: center ({center_x:.1f}, {center_y:.1f}, {center_z:.1f}), base size ({int(base_size_x)}, {int(base_size_y)}, {int(base_size_z)})")
        else:
            if not self.config_path:
                self.log("Error: Pilih config file dulu jika non-auto grid box!")
                self.finish_run()
                return
            
            config_file = Path(self.config_path).resolve()
            if not config_file.exists():
                self.log(f"Error: Config file tidak ditemukan: {config_file}")
                self.finish_run()
                return
            
            target_config = (run_dir / config_file.name).resolve()
            shutil.copy(config_file, target_config)
            config_file = target_config
            
            grid_info = {"mode": "manual", "config_file": config_file.name}
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("center_x ="):
                        grid_info["center_x"] = float(line.split("=")[1].strip())
                    elif line.startswith("center_y ="):
                        grid_info["center_y"] = float(line.split("=")[1].strip())
                    elif line.startswith("center_z ="):
                        grid_info["center_z"] = float(line.split("=")[1].strip())
                    elif line.startswith("size_x ="):
                        grid_info["size_x"] = float(line.split("=")[1].strip())
                    elif line.startswith("size_y ="):
                        grid_info["size_y"] = float(line.split("=")[1].strip())
                    elif line.startswith("size_z ="):
                        grid_info["size_z"] = float(line.split("=")[1].strip())
            self.log(f"Pakai config manual: {config_file.name}")

        # Docking
        self.log("Mulai docking...")
        pdbqt_files = list(ligands_pdbqt_dir.glob("*.pdbqt"))
        results = []

        # Test vina & obabel
        self.log("Testing executables...")
        for exe, name in [(self.vina_path, "Vina"), (self.obabel_path, "OBabel")]:
            test_cmd = [exe, "--help"]
            try:
                subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
            except Exception as e:
                self.log(f"{name} test error: {e}")
                self.finish_run()
                return

        for i, lig_pdbqt in enumerate(pdbqt_files):
            if self.stop_flag:
                self.log("Proses dihentikan")
                self.finish_run()
                return

            ligand_name = lig_pdbqt.stem
            out_pdbqt = output_dir / f"{ligand_name}_out.pdbqt"
            log_file = output_dir / f"{ligand_name}.log"
            config_file = run_dir / f"config_{ligand_name}.txt"

            if self.auto_box_var.get():
                # Calculate Rg for ligand
                rg = self.calculate_rg(lig_pdbqt)
                size_x = protein_dims["size"][0] + 2.9 * rg
                size_y = protein_dims["size"][1] + 2.9 * rg
                size_z = protein_dims["size"][2] + 2.9 * rg
                center_x, center_y, center_z = protein_dims["center"]

                config_content = f"""receptor = {protein_pdbqt.resolve()}
center_x = {center_x:.3f}
center_y = {center_y:.3f}
center_z = {center_z:.3f}
size_x = {int(size_x)}
size_y = {int(size_y)}
size_z = {int(size_z)}
exhaustiveness = {self.exhaust_var.get()}
num_modes = 10
energy_range = 4
"""
                config_file.write_text(config_content)
            else:
                config_file = Path(run_dir / grid_info["config_file"])

            cmd_dock = f'{self.vina_path} --config "{config_file.resolve()}" --ligand "{lig_pdbqt.resolve()}" --out "{out_pdbqt.resolve()}" --log "{log_file.resolve()}"'
            
            self.log(f"Docking {ligand_name}...")
            try:
                result = subprocess.run(cmd_dock, shell=True, capture_output=True, text=True, timeout=600, cwd=run_dir)
                
                if log_file.exists():
                    score = self.parse_score(str(log_file))
                    if score is not None:
                        interactions = self.analyze_interactions_detailed(self.protein_path, out_pdbqt)
                        results.append({
                            "ligand": ligand_name,
                            "score": score,
                            "interactions": interactions["residues"],
                            "detailed_interactions": interactions["detailed"]
                        })
                        
                        # Create complex
                        complex_pdb = complexes_dir / f"{ligand_name}_{protein_name}.pdb"
                        self.create_complex_pdb(self.protein_path, out_pdbqt, complex_pdb)
                else:
                    self.log(f"Log file tidak dibuat untuk {ligand_name}")
                    
            except subprocess.TimeoutExpired:
                self.log(f"Timeout docking {ligand_name}")
            except Exception as e:
                self.log(f"Error docking {ligand_name}: {e}")

            self.progressbar.set(0.2 + (i+1)/len(pdbqt_files) * 0.8)
            self.prog_label.configure(text=f"Docking {i+1}/{len(pdbqt_files)} - {len(results)} berhasil")

        # Summary & Laporan
        if results:
            results.sort(key=lambda x: x["score"])
            top_results = results[:20] if self.top_only_var.get() else results

            self.generate_summary(results, run_dir, protein_name, grid_info, self.exhaust_var.get())
            self.generate_laporan_txt(results, run_dir, protein_name, grid_info, self.exhaust_var.get())
            self.log("Summary JSON, CSV, dan laporan telah dibuat")
            self.open_folder_btn.configure(state="normal")
        else:
            self.log("Tidak ada hasil docking sukses")

        self.log(f"Screening selesai! {len(results)}/{len(pdbqt_files)} ligand berhasil")
        self.log(f"Hasil: {run_dir.resolve()}")
        self.finish_run()

    def calculate_protein_dimensions(self, protein_pdb):
        coords = []
        with open(protein_pdb, 'r') as f:
            for line in f:
                if line.startswith(("ATOM", "HETATM")):
                    try:
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                        coords.append((x, y, z))
                    except:
                        continue
        if not coords:
            return {"center": (0,0,0), "size": (40,40,40)}
        xs, ys, zs = zip(*coords)
        center_x = (min(xs) + max(xs)) / 2
        center_y = (min(ys) + max(ys)) / 2
        center_z = (min(zs) + max(zs)) / 2
        size_x = max(xs) - min(xs) + 10  # Tambah margin
        size_y = max(ys) - min(ys) + 10
        size_z = max(zs) - min(zs) + 10
        return {"center": (center_x, center_y, center_z), "size": (size_x, size_y, size_z)}

    def calculate_rg(self, lig_pdbqt):
        coords = []
        masses = []  # Approximate mass based on atom type
        atom_mass = {'C': 12, 'N': 14, 'O': 16, 'S': 32, 'H': 1, 'F': 19, 'Cl': 35.5, 'Br': 80}
        with open(lig_pdbqt, 'r') as f:
            for line in f:
                if line.startswith(("ATOM", "HETATM")):
                    try:
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                        atom_type = line[77:79].strip()
                        mass = atom_mass.get(atom_type[0], 12)  # Default to C
                        coords.append((x, y, z))
                        masses.append(mass)
                    except:
                        continue
        if not coords:
            return 5.0  # Default Rg
        total_mass = sum(masses)
        com_x = sum(m * x for (x,y,z), m in zip(coords, masses)) / total_mass
        com_y = sum(m * y for (x,y,z), m in zip(coords, masses)) / total_mass
        com_z = sum(m * z for (x,y,z), m in zip(coords, masses)) / total_mass
        rg_sq = sum(m * ((x - com_x)**2 + (y - com_y)**2 + (z - com_z)**2) for (x,y,z), m in zip(coords, masses)) / total_mass
        return sqrt(rg_sq)

    def parse_score(self, log_path):
        try:
            with open(log_path, 'r') as f:
                content = f.read()
                pattern = r'\s+1\s+([-\d\.]+)\s+'
                match = re.search(pattern, content)
                if match:
                    return float(match.group(1))
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith('1'):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            try:
                                return float(parts[1])
                            except ValueError:
                                continue
        except Exception as e:
            self.log(f"Error parsing score from {log_path}: {e}")
        return None

    def analyze_interactions_detailed(self, protein_pdb, ligand_pdbqt):
        # Load ligand atoms
        lig_atoms = []
        with open(ligand_pdbqt, 'r') as f:
            for line in f:
                if line.startswith(("ATOM", "HETATM")):
                    try:
                        atom_idx = int(line[6:11])
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                        atom_type = line[77:79].strip()
                        lig_atoms.append({"idx": atom_idx, "pos": (x,y,z), "type": atom_type})
                    except:
                        continue

        # Load protein residues
        prot_res = {}
        with open(protein_pdb, 'r') as f:
            for line in f:
                if line.startswith("ATOM"):
                    res_id = line[17:26]  # resname + resnum
                    atom_type = line[12:16].strip()
                    try:
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                        prot_res.setdefault(res_id, []).append({"type": atom_type, "pos": (x,y,z)})
                    except:
                        continue

        # Analyze interactions
        residues = set()
        detailed = []  # list of (lig_atom_idx, res_id, interaction_type)
        for lig_atom in lig_atoms:
            for res_id, res_atoms in prot_res.items():
                for res_atom in res_atoms:
                    dist = sqrt(sum((a - b)**2 for a, b in zip(lig_atom["pos"], res_atom["pos"])))
                    if dist <= 4.0:
                        residues.add(res_id.strip())
                        # Determine type
                        lig_type = lig_atom["type"][0]
                        res_type = res_atom["type"][0]
                        if (lig_type in 'ON' and res_type in 'ON') or (lig_type in 'ON' and 'H' in res_atom["type"]) or ('H' in lig_atom["type"] and res_type in 'ON'):
                            int_type = "H-bond"
                        elif lig_type in 'C' and res_type in 'C':  # Simple hydrophobic
                            int_type = "Hydrophobic"
                        elif (lig_type in 'C' and "ring" in res_id.lower()) or (res_type in 'C' and "aromatic" in lig_atom["type"].lower()):  # Dummy aromatic
                            int_type = "Aromatic"
                        else:
                            int_type = "Other"
                        detailed.append((lig_atom["idx"], res_id.strip(), int_type))
                        break  # One interaction per pair for simplicity

        return {"residues": sorted(list(residues)), "detailed": detailed}

    def create_complex_pdb(self, protein_pdb, ligand_pdbqt, output_pdb):
        temp_lig = ligand_pdbqt.with_suffix(".tmp.pdb")
        try:
            subprocess.run([self.obabel_path, "-ipdbqt", str(ligand_pdbqt), "-opdb", "-O", str(temp_lig)], 
                         capture_output=True, timeout=30)
            
            with open(output_pdb, 'w') as out:
                with open(protein_pdb, 'r') as prot:
                    for line in prot:
                        if line.startswith(("ATOM", "HETATM", "TER")):
                            out.write(line)
                if temp_lig.exists():
                    with open(temp_lig, 'r') as lig:
                        for line in lig:
                            if line.startswith(("ATOM", "HETATM")):
                                out.write("HETATM" + line[6:66] + "LIG" + line[69:])
        except Exception as e:
            self.log(f"Error creating complex: {e}")
        finally:
            if temp_lig.exists():
                temp_lig.unlink()
        
        with open(output_pdb, 'a') as f:
            f.write("END\n")

    def generate_summary(self, results, run_dir, protein_name, grid_info, exhaustiveness):
        all_contacts = [res for lig in results for res in lig["interactions"]]
        hotspot_counter = Counter(all_contacts)
        hotspot_list = [{"residue": r, "count": c, "percentage": round(c/len(results)*100, 1)}
                        for r, c in hotspot_counter.most_common()]

        top_ligands = results[:10]

        prompt = """Based on this JSON summary of virtual screening results, generate a narrative interpretation in English for a scientific journal. Structure it into two sections: 
1. 'Methods' - Describe the computational approach: blind docking virtual screening, including software used (AutoVinaEasy based on AutoDock Vina and OpenBabel), parameters (exhaustiveness, grid box method: center at protein center coordinate and size using sum of protein surface plus the 2.9 times of each ligand radius of gyration that updated for each ligand), and analysis methods.
2. 'Results and Discussion' - Summarize key findings: top ligands with scores, hotspot residues, potential binding mechanisms, and implications. Use formal scientific language."""

        summary = {
            "protein": protein_name,
            "total_ligands_screened": len(results),
            "best_score": top_ligands[0]["score"] if top_ligands else None,
            "grid": grid_info,
            "exhaustiveness": exhaustiveness,
            "hotspot_residues": hotspot_list,
            "top_ligands": [
                {
                    "rank": i+1,
                    "ligand": lig["ligand"],
                    "score": lig["score"],
                    "key_residues": lig["interactions"][:5],
                    "detailed_interactions": lig["detailed_interactions"][:10],  # Limit
                    "complex_file": f"complexes/{lig['ligand']}_{protein_name}.pdb",
                    "image_file": f"interaction_images/top{i+1:02d}_{lig['ligand']}_interaction.png"
                } for i, lig in enumerate(top_ligands)
            ],
            "prompt_for_ai": prompt
        }

        json_file = run_dir / "summary_results.json"
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2)

        csv_file = run_dir / "top_ligands.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Ligand", "Score (kcal/mol)", "Key Residues"])
            for i, lig in enumerate(top_ligands):
                writer.writerow([i+1, lig["ligand"], lig["score"], ", ".join(lig["interactions"][:5])])

        hotspot_csv = run_dir / "hotspot_frequency.csv"
        with open(hotspot_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Residue", "Count", "Percentage (%)"])
            for item in hotspot_list:
                writer.writerow([item["residue"], item["count"], item["percentage"]])

    def generate_laporan_txt(self, results, run_dir, protein_name, grid_info, exhaustiveness):
        top_ligands = results[:10]
        all_contacts = [res for lig in results for res in lig["interactions"]]
        hotspot_counter = Counter(all_contacts)
        hotspot_list = hotspot_counter.most_common()

        laporan = f"""
VIRTUAL SCREENING SUMMARY - AutoVinaEasy Pipeline
==================================================

Protein Target      : {protein_name}
Total Ligands Screened : {len(results)}
Best Docking Score     : {top_ligands[0]['score'] if top_ligands else 'N/A'} kcal/mol

Metode Docking:
Blind docking virtual screening performed using platform AutoVinaEasy (Yaqin, 2026) based on AutoDock Vina and OpenBabel with grid box: center ({grid_info.get('center', [0,0,0])[0]:.1f}, {grid_info.get('center', [0,0,0])[1]:.1f}, {grid_info.get('center', [0,0,0])[2]:.1f}), base size ({grid_info.get('base_size', [0,0,0])[0]}, {grid_info.get('base_size', [0,0,0])[1]}, {grid_info.get('base_size', [0,0,0])[2]}), adjusted per ligand with 2.9*Rg, exhaustiveness = {exhaustiveness}.

TOP 10 LIGANDS
--------------
Rank | Ligand ID         | Score (kcal/mol) | Key Interacting Residues (top 5)
"""
        for i, lig in enumerate(top_ligands):
            laporan += f"{i+1:<4} | {lig['ligand']:<17} | {lig['score']:<16} | {', '.join(lig['interactions'][:5])}\n"

        laporan += f"""
HOTSPOT RESIDUE ANALYSIS (Frequency from {'top 20' if self.top_only_var.get() else 'all'} ligands)
-----------------------------------------------------------
Residue   | Times Contacted | Percentage (%) 
"""
        for res, count in hotspot_list:
            perc = round(count / len(results) * 100, 1)
            laporan += f"{res:<9} | {count:<15} | {perc}\n"

        laporan += f"""
INTERPRETATION
--------------
The binding pocket is characterized by residues {', '.join([r for r, _ in hotspot_list[:5]])} which appear critical for ligand binding. Top compounds predominantly form interactions with these key residues, suggesting potential competitive inhibition mechanisms.

Note: These are computational predictions and require experimental validation.
"""

        laporan_file = run_dir / f"{protein_name}_laporan.txt"
        with open(laporan_file, 'w') as f:
            f.write(laporan)

    def finish_run(self):
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.progressbar.set(1)
        self.prog_label.configure(text="Progress: Completed")

if __name__ == "__main__":
    app = VirtualScreeningApp()
    app.mainloop()