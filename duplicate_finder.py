import os
import sys
import hashlib
from pathlib import Path
from collections import defaultdict

# Folder yang TIDAK BOLEH di-scan+hapus sama sekali (proteksi).
PROTECTED_FOLDERS = {
    "/", "/root", "/home", "/etc", "/usr", "/bin", "/sbin", "/lib",
    "/System", "/Library", "/Applications", "/Windows",
    "C:\\", "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",
}

CHUNK_SIZE = 8192  # baca file per 8KB biar hemat memori buat file besar


def get_common_folders():
    home = Path.home()
    candidates = {
        "Downloads": home / "Downloads",
        "Documents": home / "Documents",
        "Desktop": home / "Desktop",
        "Pictures": home / "Pictures",
    }
    return {name: str(path) for name, path in candidates.items() if path.is_dir()}


def is_protected(folder_path):
    resolved = str(Path(folder_path).resolve())
    home_resolved = str(Path.home().resolve())

    if resolved in PROTECTED_FOLDERS:
        return True
    if resolved == home_resolved:
        return True
    if len(resolved) <= 3 and resolved.endswith(":\\"):
        return True
    return False


def choose_folder_interactively():
    common = get_common_folders()

    print("Folder mana yang mau di-scan untuk cari file duplikat?\n")
    options = list(common.items())
    for i, (name, path) in enumerate(options, start=1):
        print(f"  {i}. {name}  ({path})")
    print(f"  {len(options) + 1}. Masukkan path folder lain secara manual")

    choice = input("\nPilih nomor: ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(options):
        return options[int(choice) - 1][1]
    else:
        manual_path = input("Masukkan path lengkap folder: ").strip().strip('"')
        return manual_path


def hash_file(filepath):
    """Hitung SHA-256 dari isi file. Return None kalau gagal dibaca."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError) as e:
        print(f"  (dilewati, gagal dibaca: {os.path.basename(filepath)} — {e})")
        return None


def find_duplicates(folder_path, recursive=True):
    """Scan folder, kelompokkan file berdasarkan hash isinya.
    Return dict: {hash: [list of filepaths]} — hanya yang punya >1 file (duplikat)."""
    hashes = defaultdict(list)

    if recursive:
        walker = os.walk(folder_path)
    else:
        walker = [(folder_path, [], os.listdir(folder_path))]

    file_count = 0
    for root, _, files in walker:
        for filename in files:
            if filename.startswith("."):
                continue
            filepath = os.path.join(root, filename)
            file_count += 1
            file_hash = hash_file(filepath)
            if file_hash:
                hashes[file_hash].append(filepath)

    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    return duplicates, file_count


def format_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}TB"


def report_duplicates(duplicates):
    if not duplicates:
        print("\nGak ada file duplikat ditemukan. Bersih!")
        return 0

    total_wasted = 0
    group_num = 1

    for file_hash, paths in duplicates.items():
        file_size = os.path.getsize(paths[0])
        wasted = file_size * (len(paths) - 1)  # yang "boros" = semua salinan kecuali 1
        total_wasted += wasted

        print(f"\nGrup #{group_num} — {len(paths)} file identik ({format_size(file_size)} each):")
        for i, path in enumerate(paths):
            marker = "[SIMPAN]" if i == 0 else "[DUPLIKAT]"
            print(f"  {marker} {path}")
        group_num += 1

    print(f"\n{'=' * 50}")
    print(f"Total {len(duplicates)} grup duplikat ditemukan.")
    print(f"Potensi ruang yang bisa dihemat: {format_size(total_wasted)}")
    return len(duplicates)


def delete_duplicates_interactively(duplicates):
    """Untuk tiap grup, file pertama otomatis disimpan (jadi 'master'),
    sisanya ditawarkan untuk dihapus — dengan konfirmasi per grup."""
    if not duplicates:
        return

    confirm_all = input(
        "\nMau hapus file duplikat sekarang? File PERTAMA di tiap grup akan "
        "disimpan, sisanya dihapus. (y = tanya per grup / n = skip semua): "
    ).strip().lower()

    if confirm_all != "y":
        print("Gak ada yang dihapus.")
        return

    deleted_count = 0
    freed_space = 0

    for file_hash, paths in duplicates.items():
        keep = paths[0]
        to_delete = paths[1:]

        print(f"\nSimpan: {keep}")
        for path in to_delete:
            answer = input(f"  Hapus '{path}'? (y/n): ").strip().lower()
            if answer == "y":
                try:
                    size = os.path.getsize(path)
                    os.remove(path)
                    print(f"  Dihapus: {path}")
                    deleted_count += 1
                    freed_space += size
                except OSError as e:
                    print(f"  GAGAL hapus '{path}': {e}")

    print(f"\nSelesai! {deleted_count} file dihapus, {format_size(freed_space)} ruang dihemat.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_folder = sys.argv[1]
    else:
        target_folder = choose_folder_interactively()

    if not target_folder or not os.path.isdir(target_folder):
        print("Folder tidak valid atau tidak ditemukan. Keluar.")
        sys.exit(1)

    if is_protected(target_folder):
        print(f"\nDIBATALKAN: '{target_folder}' adalah folder sistem/home yang dilindungi.")
        sys.exit(1)

    print(f"\nMemindai: {target_folder}\n")
    duplicates, total_files = find_duplicates(target_folder)
    print(f"\nTotal {total_files} file dipindai.")

    num_groups = report_duplicates(duplicates)

    if num_groups > 0:
        delete_duplicates_interactively(duplicates)
