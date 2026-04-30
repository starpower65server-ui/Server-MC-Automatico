import os
import platform
import urllib.request
import urllib.parse
import json
import time

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_console()
    print("="*50)
    print("   INSTALADOR AUTOMÁTICO DE SERVIDOR MINECRAFT")
    print("="*50)
    
    # 1. Detectar el Sistema Operativo
    sys_os = platform.system()
    if sys_os == 'Windows':
        print("[+] Sistema detectado: Windows")
    elif sys_os == 'Linux':
        print("[+] Sistema detectado: Linux")
    else:
        print(f"[+] Sistema detectado: {sys_os}")

    print("\n[*] Conectando a los servidores oficiales de Mojang...")
    
    # 2. Conectar a la API de Mojang para obtener versiones
    try:
        req = urllib.request.urlopen("https://launchermeta.mojang.com/mc/game/version_manifest.json")
        data = json.loads(req.read())
    except Exception as e:
        print(f"[-] Error al conectar con Mojang: {e}")
        return

    # Filtrar para solo mostrar versiones lanzadas (release) y no snapshots
    releases = [v for v in data['versions'] if v['type'] == 'release']
    
    print("\n[+] Versiones principales disponibles:")
    for i, v in enumerate(releases):
        print(f"  {i+1}. Minecraft {v['id']}")
    
    # 3. Preguntar por la versión
    seleccion = input(f"\n[?] Escribe la versión exacta que quieres (ej: 1.20.4) o el número de la lista (1-{len(releases)}): ")
    
    version_obj = None
    if seleccion.isdigit() and 1 <= int(seleccion) <= len(releases):
        version_obj = releases[int(seleccion)-1]
    else:
        for v in releases:
            if v['id'] == seleccion:
                version_obj = v
                break
                
    if not version_obj:
        print("[-] Versión no encontrada o entrada inválida. Cancelando instalación.")
        return
        
    print(f"\n[*] Preparando la descarga para la versión {version_obj['id']}...")
    
    # 4. Obtener el link de descarga directo y descargar
    try:
        v_req = urllib.request.urlopen(version_obj['url'])
        v_data = json.loads(v_req.read())
        
        if 'downloads' in v_data and 'server' in v_data['downloads']:
            server_url = v_data['downloads']['server']['url']
            print("[*] Descargando server.jar oficial (Esto puede tardar unos segundos dependiendo de tu internet)...")
            
            # Descargamos el archivo
            urllib.request.urlretrieve(server_url, "server.jar")
            print("[+] ¡server.jar descargado con éxito!")
        else:
            print("[-] Esta versión es demasiado antigua o no tiene servidor oficial.")
            return
    except Exception as e:
        print(f"[-] Error descargando el servidor: {e}")
        return

    # 5. Aceptar EULA automáticamente
    print("\n[*] Creando y aceptando eula.txt automáticamente...")
    with open("eula.txt", "w") as f:
        f.write("# By changing the setting below to TRUE you are indicating your agreement to our ELA.\n")
        f.write("eula=true\n")
        
    # 6. Configurar la Conexión (Red Local o Tailscale)
    print("\n[?] ¿Cómo se conectarán tus amigos al servidor?")
    print("  1. Red Local (LAN) o abriendo puertos (Automático)")
    print("  2. Tailscale (Se configurará automáticamente tu IP de Tailscale)")
    print("  3. Otra VPN / IP Manual")
    
    opcion_ip = input("Elige una opción (1/2/3) [Por defecto: 1]: ").strip()
    ip_input = ""
    
    if opcion_ip == "2":
        print("[*] Buscando instalación de Tailscale...")
        try:
            ts_ip = os.popen('tailscale ip -4').read().strip()
            if ts_ip and "." in ts_ip:
                ip_input = ts_ip
                print(f"[+] ¡Tailscale detectado! Tu servidor solo escuchará en la IP: {ip_input}")
            else:
                print("[-] Tailscale no respondió correctamente o no está instalado.")
                descargar = input("[?] ¿Deseas descargar e instalar Tailscale ahora? (s/n): ").strip().lower()
                if descargar == 's':
                    if sys_os == 'Windows':
                        print("[*] Descargando el instalador de Tailscale (tailscale-setup.exe)...")
                        try:
                            urllib.request.urlretrieve("https://pkgs.tailscale.com/stable/tailscale-setup-latest.exe", "tailscale-setup.exe")
                            print("[+] Instalador descargado. Abriendo instalador...")
                            os.startfile("tailscale-setup.exe")
                        except Exception as e:
                            print(f"[-] Error descargando: {e}")
                        print("\n[!] IMPORTANTE: Completa los pasos del instalador que se acaba de abrir.")
                        print("[!] Cuando termine, asegúrate de iniciar sesión en Tailscale desde la barra de tareas (el icono abajo a la derecha).")
                        input("-> Presiona ENTER ÚNICAMENTE cuando Tailscale esté conectado y hayas iniciado sesión...")
                    else:
                        print("[*] Instalando Tailscale en Linux...")
                        os.system("curl -fsSL https://tailscale.com/install.sh | sh")
                        print("[*] Iniciando el demonio de Tailscale...")
                        os.system("sudo tailscaled &")
                        import time
                        time.sleep(2)
                        print("[*] Iniciando sesión en Tailscale...")
                        os.system("sudo tailscale up")
                        print("\n[!] IMPORTANTE: Si Tailscale te pidió iniciar sesión, complétalo desde el navegador.")
                        input("-> Presiona ENTER cuando hayas terminado de conectar tu cuenta...")
                    
                    print("[*] Verificando de nuevo si Tailscale está listo...")
                    ts_ip = os.popen('tailscale ip -4').read().strip()
                    if ts_ip and "." in ts_ip:
                        ip_input = ts_ip
                        print(f"[+] ¡Perfecto! Tailscale detectado exitosamente. IP asignada: {ip_input}")
                    else:
                        print("[-] No se pudo autodetectar la IP. Quizás aún está iniciando.")
                        ip_input = input("[?] Escribe tu IP de Tailscale manualmente (o Enter para automático): ").strip()
                else:
                    ip_input = input("[?] Escribe tu IP de Tailscale manualmente (o Enter para automático): ").strip()
        except Exception:
            ip_input = input("[?] Escribe tu IP manualmente (o Enter para automático): ").strip()
    elif opcion_ip == "3":
        ip_input = input("[?] Escribe la IP específica a usar: ").strip()
    
    # Leer server.properties si existe, o crear de cero
    properties_lines = []
    if os.path.exists("server.properties"):
        with open("server.properties", "r") as f:
            properties_lines = f.readlines()
            
    ip_found = False
    for i in range(len(properties_lines)):
        if properties_lines[i].startswith("server-ip="):
            properties_lines[i] = f"server-ip={ip_input}\n"
            ip_found = True
            break
            
    # + Configurar RCON (para el botón de apagado automático)
    rcon_config = {
        "enable-rcon=": "enable-rcon=true\n",
        "rcon.password=": "rcon.password=admin\n",
        "rcon.port=": "rcon.port=25575\n"
    }

    for key, val in rcon_config.items():
        found = False
        for i in range(len(properties_lines)):
            if properties_lines[i].startswith(key):
                properties_lines[i] = val
                found = True
                break
        if not found:
            properties_lines.append(val)
            
    with open("server.properties", "w") as f:
        f.writelines(properties_lines)
        
    print(f"[+] Archivo server.properties actualizado. (IP configurada: {'Automático' if ip_input == '' else ip_input})")
    
    # 7. Crear los iniciadores y botones de control
    print("\n[*] Creando botones de control (start, backup, apagar)...")
    with open("start.bat", "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("title Servidor de Minecraft\n")
        f.write("java -Xmx2G -Xms2G -jar server.jar nogui\n")
        f.write("pause\n")
        
    with open("start.sh", "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write("java -Xmx2G -Xms2G -jar server.jar nogui\n")
        
    # Script de RCON en Python (usado por el botón de apagado)
    rcon_py = '''import socket, struct, time
def send_rcon(host, port, password, command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((host, port))
        l_pack = struct.pack('<ii', 1, 3) + password.encode('utf-8') + b'\\x00\\x00'
        s.sendall(struct.pack('<i', len(l_pack)) + l_pack)
        s.recv(4096)
        c_pack = struct.pack('<ii', 2, 2) + command.encode('utf-8') + b'\\x00\\x00'
        s.sendall(struct.pack('<i', len(c_pack)) + c_pack)
        s.recv(4096)
    finally:
        s.close()
try:
    print(">> Guardando mundo de Minecraft...")
    send_rcon('127.0.0.1', 25575, 'admin', 'save-all')
    time.sleep(1)
    print(">> Apagando servidor...")
    send_rcon('127.0.0.1', 25575, 'admin', 'stop')
    print("====== ¡Servidor apagado de forma segura! ======")
except Exception as e:
    print("Error: El servidor ya esta apagado o todavia no se ha encendido del todo.")
    print("Detalle:", e)
time.sleep(3)
'''
    with open("apagar_servidor.py", "w", encoding="utf-8") as f:
        f.write(rcon_py)

    # Windows: backup y apagar
    with open("hacer_backup.bat", "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write('echo Creando una copia de seguridad en formato ZIP...\n')
        f.write('if not exist backups mkdir backups\n')
        f.write('set stamp=%date:/=-%_%time::=-%\n')
        f.write('set stamp=%stamp: =0%\n')
        f.write('set stamp=%stamp:,=-%\n')
        f.write('set stamp=%stamp:.=-%\n')
        f.write('powershell Compress-Archive -Path world -DestinationPath "backups\\mundo_backup_%stamp%.zip" -Force\n')
        f.write('echo Backup completado en la carpeta backups.\n')
        f.write('pause\n')

    with open("apagar_servidor.bat", "w", encoding="utf-8") as f:
        f.write("@echo off\npython apagar_servidor.py\n")

    # Linux: backup y apagar
    with open("hacer_backup.sh", "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Creando copia de seguridad...'\n")
        f.write("mkdir -p backups\n")
        f.write("zip -r backups/mundo_backup_$(date +%Y%m%d_%H%M%S).zip world\n")
        f.write("echo 'Backup completado.'\n")

    with open("apagar_servidor.sh", "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\npython3 apagar_servidor.py\n")

    if sys_os != 'Windows':
        try:
            os.chmod("start.sh", 0o755)
            os.chmod("hacer_backup.sh", 0o755)
            os.chmod("apagar_servidor.sh", 0o755)
        except Exception:
            pass

    # 8. Instalar Mods (opcional)
    instalar_mods = input("\n[?] ¿Quieres instalar mods en tu servidor? (s/n) [Por defecto: n]: ").strip().lower()
    if instalar_mods == 's':
        instalar_mods_menu(version_obj['id'], sys_os)

    # Finalización
    print("\n" + "="*50)
    print("  ¡INSTALACIÓN COMPLETADA CON ÉXITO!  ")
    print("="*50)
    print("Se han creado los siguientes botones mágicos para que uses:")
    print(" 1. > start (Enciende el servidor Minecraft)")
    print(" 2. > hacer_backup (Comprime tu mundo en un .zip sin apagar nada)")
    print(" 3. > apagar_servidor (Apaga el juego forzando el guardado de seguridad)")
    print("\nTu servidor está 100% listo para arrancar.\n")
    if sys_os == 'Windows':
        print("Para encenderlo, simplemente haz doble clic en el archivo 'start.bat'.")
    else:
        print("Para encenderlo, ejecuta en la terminal el archivo './start.sh' en esta carpeta.")
        
    input("\nPresiona ENTER para salir...")

# ──────────────────────────────────────────────
#  MÓDULO DE INSTALACIÓN DE MODS
# ──────────────────────────────────────────────

def instalar_mods_menu(mc_version, sys_os):
    """Menú principal de instalación de mods."""
    print("\n" + "="*50)
    print("   INSTALADOR DE MODS")
    print("="*50)
    print("\nPara usar mods en un servidor necesitas un 'mod loader'.")
    print("Los más populares son:")
    print("  1. Fabric  (ligero, mods modernos de rendimiento)")
    print("  2. Forge   (el clásico, la mayor biblioteca de mods)")
    print("  3. Cancelar (mantener servidor vanilla)")

    opcion_loader = input("\n[?] Elige el loader (1/2/3): ").strip()

    if opcion_loader == '1':
        loader = 'fabric'
        exito = instalar_fabric(mc_version, sys_os)
    elif opcion_loader == '2':
        loader = 'forge'
        exito = instalar_forge(mc_version, sys_os)
    else:
        print("[*] Cancelado. El servidor se quedará vanilla.")
        return

    if not exito:
        print("[-] No se pudo instalar el loader. Los mods no estarán disponibles.")
        return

    # Crear carpeta de mods
    os.makedirs("mods", exist_ok=True)
    print("[+] Carpeta 'mods/' lista.")

    # Bucle de búsqueda e instalación de mods
    buscar_e_instalar_mods(mc_version, loader)


def instalar_fabric(mc_version, sys_os):
    """Descarga e instala el servidor de Fabric para la versión dada."""
    print(f"\n[*] Buscando la versión de Fabric compatible con Minecraft {mc_version}...")
    try:
        # API de Fabric: obtener versiones del loader
        req = urllib.request.urlopen("https://meta.fabricmc.net/v2/versions/loader")
        loaders = json.loads(req.read())
        # Usar el loader estable más reciente
        loader_version = None
        for l in loaders:
            if l.get('stable', False):
                loader_version = l['version']
                break
        if not loader_version:
            loader_version = loaders[0]['version']

        # Obtener versiones del installer de Fabric
        req2 = urllib.request.urlopen("https://meta.fabricmc.net/v2/versions/installer")
        installers = json.loads(req2.read())
        installer_version = None
        for inst in installers:
            if inst.get('stable', False):
                installer_version = inst['version']
                break
        if not installer_version:
            installer_version = installers[0]['version']

        print(f"[+] Loader Fabric: {loader_version} | Installer: {installer_version}")

        # Descargar el JAR del servidor de Fabric
        fabric_jar_url = (
            f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}/"
            f"{loader_version}/{installer_version}/server/jar"
        )
        print("[*] Descargando fabric-server.jar...")
        urllib.request.urlretrieve(fabric_jar_url, "fabric-server.jar")
        print("[+] ¡fabric-server.jar descargado!")

        # Actualizar los scripts de arranque para usar fabric
        _actualizar_scripts_inicio("fabric-server.jar", sys_os)
        print("[+] Scripts de inicio actualizados para usar Fabric.")
        return True

    except Exception as e:
        print(f"[-] Error instalando Fabric: {e}")
        return False


def instalar_forge(mc_version, sys_os):
    """Descarga el instalador de Forge y lo ejecuta."""
    print(f"\n[*] Buscando versiones de Forge para Minecraft {mc_version}...")
    try:
        # Usar la API de Forge Maven
        forge_api_url = f"https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
        req = urllib.request.urlopen(forge_api_url)
        promos = json.loads(req.read()).get('promos', {})

        # Intentar obtener la versión recomendada o la más reciente para mc_version
        forge_version = (
            promos.get(f"{mc_version}-recommended") or
            promos.get(f"{mc_version}-latest")
        )

        if not forge_version:
            print(f"[-] No se encontró una versión de Forge para Minecraft {mc_version}.")
            print("[!] Puedes descargarla manualmente en: https://files.minecraftforge.net")
            return False

        full_forge_version = f"{mc_version}-{forge_version}"
        installer_name = f"forge-{full_forge_version}-installer.jar"
        installer_url = (
            f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
            f"{full_forge_version}/{installer_name}"
        )

        print(f"[+] Forge encontrado: {full_forge_version}")
        print("[*] Descargando instalador de Forge...")
        urllib.request.urlretrieve(installer_url, installer_name)
        print(f"[+] Instalador descargado: {installer_name}")

        print("[*] Ejecutando el instalador de Forge (modo --installServer)...")
        ret = os.system(f'java -jar "{installer_name}" --installServer')
        if ret != 0:
            print("[-] El instalador de Forge devolvió un error. Verifica que Java esté instalado.")
            return False

        # Forge crea un jar con un nombre específico; actualizar scripts
        # Nombre típico: forge-<version>.jar o run.sh/run.bat
        forge_jar = f"forge-{full_forge_version}.jar"
        if os.path.exists(forge_jar):
            _actualizar_scripts_inicio(forge_jar, sys_os)
        elif os.path.exists("run.sh") or os.path.exists("run.bat"):
            print("[+] Forge generó scripts 'run.sh'/'run.bat'. Úsalos para arrancar el servidor.")
        else:
            print("[!] Usa el jar de Forge generado para arrancar el servidor.")

        print("[+] ¡Forge instalado correctamente!")
        return True

    except Exception as e:
        print(f"[-] Error instalando Forge: {e}")
        return False


def _actualizar_scripts_inicio(jar_name, sys_os):
    """Sobrescribe start.sh y start.bat para apuntar al nuevo JAR del loader."""
    with open("start.bat", "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("title Servidor de Minecraft\n")
        f.write(f'java -Xmx2G -Xms2G -jar "{jar_name}" nogui\n')
        f.write("pause\n")

    with open("start.sh", "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write(f'java -Xmx2G -Xms2G -jar "{jar_name}" nogui\n')

    if sys_os != 'Windows':
        try:
            os.chmod("start.sh", 0o755)
        except Exception:
            pass


def buscar_e_instalar_mods(mc_version, loader):
    """Bucle interactivo para buscar mods en Modrinth e instalarlos."""
    print("\n" + "-"*50)
    print(f"  BUSCADOR DE MODS (Modrinth) — MC {mc_version} / {loader.capitalize()}")
    print("-"*50)
    print("Escribe el nombre de un mod para buscarlo, o 'salir' para terminar.\n")

    while True:
        query = input("[?] Nombre del mod (o 'salir'): ").strip()
        if query.lower() in ('salir', 'exit', 'q', ''):
            print("[*] Saliendo del instalador de mods.")
            break

        resultados = buscar_mod_modrinth(query, mc_version, loader)
        if not resultados:
            print("[-] No se encontraron mods con ese nombre para tu versión/loader.")
            continue

        print(f"\n[+] Se encontraron {len(resultados)} resultado(s):")
        for i, mod in enumerate(resultados):
            descargas = mod.get('downloads', 0)
            desc = mod.get('description', '')[:60]
            print(f"  {i+1}. {mod['title']} ({descargas:,} descargas) — {desc}")

        sel = input(f"\n[?] Elige un número para instalar (1-{len(resultados)}), o ENTER para nueva búsqueda: ").strip()
        if not sel.isdigit() or not (1 <= int(sel) <= len(resultados)):
            print("[*] Volviendo al buscador...")
            continue

        mod_elegido = resultados[int(sel) - 1]
        descargar_mod_modrinth(mod_elegido, mc_version, loader)


def buscar_mod_modrinth(query, mc_version, loader):
    """Busca mods en la API de Modrinth y devuelve hasta 8 resultados."""
    try:
        # facets: tipo mod, compatible con mc_version y el loader
        facets = json.dumps([[f"project_type:mod"], [f"versions:{mc_version}"], [f"categories:{loader}"]])
        params = urllib.parse.urlencode({
            'query': query,
            'limit': 8,
            'facets': facets
        })
        url = f"https://api.modrinth.com/v2/search?{params}"
        req = urllib.request.Request(url, headers={'User-Agent': 'MinecraftServerInstaller/1.0'})
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        return data.get('hits', [])
    except Exception as e:
        print(f"[-] Error al buscar en Modrinth: {e}")
        return []


def descargar_mod_modrinth(mod, mc_version, loader):
    """Descarga la versión más reciente compatible de un mod desde Modrinth."""
    project_id = mod['project_id']
    mod_title = mod['title']
    print(f"\n[*] Buscando la versión descargable de '{mod_title}'...")
    try:
        params = urllib.parse.urlencode({
            'game_versions': json.dumps([mc_version]),
            'loaders': json.dumps([loader])
        })
        url = f"https://api.modrinth.com/v2/project/{project_id}/version?{params}"
        req = urllib.request.Request(url, headers={'User-Agent': 'MinecraftServerInstaller/1.0'})
        resp = urllib.request.urlopen(req)
        versiones = json.loads(resp.read())

        if not versiones:
            print(f"[-] No hay versiones de '{mod_title}' para MC {mc_version} con {loader}.")
            return

        # Tomar la primera versión (más reciente)
        version = versiones[0]
        files = version.get('files', [])
        # Preferir el archivo marcado como primary
        archivo = next((f for f in files if f.get('primary')), files[0] if files else None)

        if not archivo:
            print(f"[-] No se encontró archivo descargable para '{mod_title}'.")
            return

        file_url = archivo['url']
        file_name = archivo['filename']
        dest = os.path.join("mods", file_name)

        if os.path.exists(dest):
            print(f"[!] El mod '{file_name}' ya existe en la carpeta mods/. Saltando.")
            return

        print(f"[*] Descargando {file_name}...")
        urllib.request.urlretrieve(file_url, dest)
        print(f"[+] ¡'{mod_title}' instalado correctamente en mods/{file_name}!")

    except Exception as e:
        print(f"[-] Error descargando '{mod_title}': {e}")


if __name__ == "__main__":
    main()
