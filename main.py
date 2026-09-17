import sys
import os

import organizer
import duplicate_finder


def print_banner():
    print("=" * 50)
    print("   TOOLKIT — File Management Tools")
    print("=" * 50)


def print_menu():
    print("\nMau pakai tool yang mana?\n")
    print("  1. Rapikan file (organize by type)")
    print("  2. Cari & hapus file duplikat")
    print("  0. Keluar")


def run_organizer():
    target_folder = organizer.choose_folder_interactively()

    if not target_folder or not os.path.isdir(target_folder):
        print("Folder tidak valid atau tidak ditemukan.")
        return

    if organizer.is_protected(target_folder):
        print(f"\nDIBATALKAN: '{target_folder}' adalah folder sistem/home yang dilindungi.")
        return

    confirm = input(
        f"\nFolder yang akan dirapikan: {target_folder}\n"
        f"Lanjutkan? Ini akan MEMINDAHKAN file (bukan copy). (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("Dibatalkan.")
        return

    organizer.organize_folder(target_folder)


def run_duplicate_finder():
    target_folder = duplicate_finder.choose_folder_interactively()

    if not target_folder or not os.path.isdir(target_folder):
        print("Folder tidak valid atau tidak ditemukan.")
        return

    if duplicate_finder.is_protected(target_folder):
        print(f"\nDIBATALKAN: '{target_folder}' adalah folder sistem/home yang dilindungi.")
        return

    print(f"\nMemindai: {target_folder}\n")
    duplicates, total_files = duplicate_finder.find_duplicates(target_folder)
    print(f"\nTotal {total_files} file dipindai.")

    num_groups = duplicate_finder.report_duplicates(duplicates)

    if num_groups > 0:
        duplicate_finder.delete_duplicates_interactively(duplicates)


def main():
    print_banner()

    while True:
        print_menu()
        choice = input("\nPilih nomor: ").strip()

        if choice == "1":
            run_organizer()
        elif choice == "2":
            run_duplicate_finder()
        elif choice == "0":
            print("\nSampai jumpa!")
            sys.exit(0)
        else:
            print("Pilihan tidak valid, coba lagi.")

        input("\nTekan Enter untuk kembali ke menu...")


if __name__ == "__main__":
    main()
