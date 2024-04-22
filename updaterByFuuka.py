import paramiko
from scp import SCPClient
import tkinter as tk
from tkinter import filedialog
import sys
import os
import shutil
from colorama import init, Fore, Style
from tqdm import tqdm

# Инициализируем colorama
init(autoreset=True)

def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def list_remote_dir(sftp, remote_dir):
    try:
        remote_files = sftp.listdir_attr(remote_dir)
        return [(file.filename, (file.st_mode & 0o40000) == 0o40000) for file in remote_files]
    except FileNotFoundError as e:
        print(Fore.RED + f"Ошибка: удаленная директория не найдена {remote_dir}")
        return []

def sync_local_directory_with_remote(ssh_client, remote_dir, local_dir):
    with SCPClient(ssh_client.get_transport()) as scp:
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        sftp = ssh_client.open_sftp()
        remote_items = list_remote_dir(sftp, remote_dir)
        remote_names = [item[0] for item in remote_items]

        # Удаление локальных файлов и папок
        local_items = os.listdir(local_dir)
        for item in local_items:
            if item not in remote_names:
                local_item_path = os.path.join(local_dir, item)
                if os.path.isdir(local_item_path):
                    print(Fore.YELLOW + f"Удаление локальной директории: {local_item_path}")
                    shutil.rmtree(local_item_path)
                else:
                    print(Fore.YELLOW + f"Удаление локального файла: {local_item_path}")
                    os.remove(local_item_path)

        # Загрузка и обновление файлов
        for remote_item, is_directory in tqdm(remote_items, desc="Синхронизация", unit="file"):
            remote_item_path = os.path.join(remote_dir, remote_item).replace("\\", "/")
            local_item_path = os.path.join(local_dir, remote_item)
            
            if is_directory:
                if not os.path.exists(local_item_path):
                    os.makedirs(local_item_path)
                sync_local_directory_with_remote(ssh_client, remote_item_path, local_item_path)
            else:
                if not os.path.exists(local_item_path):
                    print(Fore.GREEN + f"Загрузка: {remote_item_path} -> {local_item_path}")
                    scp.get(remote_item_path, local_item_path)
                else:
                    print(Fore.CYAN + f"Файл уже существует: {local_item_path}")
        sftp.close()

def choose_directory():
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    return folder_selected

def main():
    print(Style.BRIGHT + Fore.MAGENTA + "Добро пожаловать в программу обновления Minecraft! By Fuuka")
    print(Style.BRIGHT + Fore.MAGENTA + "(это альфа версия программы)")
    print(Style.BRIGHT + Fore.MAGENTA + "Нажмите '1', чтобы указать папку .minecraft для обновления файлов.")
    print(Style.BRIGHT + Fore.MAGENTA + "(Рекомендуется использовать чистую версию игры)")

    choice = input(Style.BRIGHT + "Ваш выбор: ")
    if choice == '1':
        local_base_path = choose_directory()
        if not local_base_path:
            print(Fore.RED + "Директория не выбрана.")
            return

        server = "0.0.0.0" # Адресс сервера
        port = 22 # Порт сервера
        user = "ssh_user" # SSH пользователь
        password = "ssh_password" # SSH пароль
        remote_base_path = "/home/files/" # Путь до папок

        ssh_client = create_ssh_client(server, port, user, password)

        for folder in ["shaderpacks", "resourcepacks", "mods", "config"]: # Папки которые необходимо синхронизировать
            local_folder_path = os.path.join(local_base_path, folder)
            print(Style.BRIGHT + Fore.BLUE + f"Загружается {folder}...")
            sync_local_directory_with_remote(ssh_client, f"{remote_base_path}/{folder}", local_folder_path)

        print(Style.BRIGHT + Fore.GREEN + "Загрузка завершена.")
        input("Нажмите enter чтобы закрыть окно.")
    else:
        print(Fore.RED + "Обновление отменено.")
        sys.exit()

if __name__ == "__main__":
    main()
