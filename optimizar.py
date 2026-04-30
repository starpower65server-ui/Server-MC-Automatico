import os
import platform
import subprocess
import glob

def get_total_ram_gb():
    """Detecta la cantidad total de memoria RAM física instalada en GB."""
    sys_os = platform.system()
    try:
        if sys_os == 'Windows':
            output = subprocess.check_output('wmic computersystem get TotalPhysicalMemory', shell=True).decode()
            lines = output.strip().split('\n')
            bytes_ram = int(lines[-1].strip())
            return bytes_ram / (1024**3)
        elif sys_os == 'Linux':
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        kb_ram = int(line.split()[1])
                        return kb_ram / (1024**2)
    except Exception as e:
        print(f"[-] No se pudo detectar la memoria RAM automáticamente: {e}")
    return None

def main():
    # Limpiar pantalla
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("="*50)
    print("   OPTIMIZADOR AUTOMÁTICO DE SERVIDOR MINECRAFT")
    print("="*50)

    # 1. Detectar hardware (RAM)
    ram_gb = get_total_ram_gb()
    if ram_gb is None:
        print("[-] Fallo al detectar la RAM. Usaremos 2GB por defecto.")
        allocated_ram = 2
    else:
        print(f"[+] Memoria RAM total detectada: {ram_gb:.2f} GB")
        # Dejamos 1.5 GB o 2 GB libres para el sistema operativo
        if ram_gb <= 4:
            allocated_ram = max(1, int(ram_gb - 1))
        else:
            allocated_ram = int(ram_gb - 2)
            
        # No suele ser necesario más de 12GB para un servidor normal de Minecraft, 
        # usar más puede generar pausas por el Garbage Collector de Java
        if allocated_ram > 12:
            allocated_ram = 12
            
    print(f"[+] Se asignarán {allocated_ram} GB de RAM al servidor Minecraft.")

    # 2. Banderas de Aikar (Las mejores banderas de optimización de Java para Minecraft)
    print("\n[*] Generando scripts de inicio con Aikar's Flags (Optimización de Java)...")
    aikar_flags = (
        f"-Xms{allocated_ram}G -Xmx{allocated_ram}G -XX:+UseG1GC "
        "-XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 "
        "-XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC "
        "-XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 "
        "-XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 "
        "-XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 "
        "-XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 "
        "-XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 "
        "-XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 "
        "-Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true"
    )

    # 3. Buscar el archivo jar principal del servidor
    jar_name = "server.jar"
    
    # Comprobar si se está usando Fabric o Forge para arrancar el mod loader en lugar del vanilla
    for f in os.listdir('.'):
        if f.startswith('fabric-server') and f.endswith('.jar'):
            jar_name = f
            break
        elif f.startswith('forge-') and f.endswith('.jar') and 'installer' not in f:
            jar_name = f
            break
            
    print(f"[*] Archivo .jar detectado para arrancar: {jar_name}")

    # 4. Escribir y sobrescribir start.bat y start.sh
    with open("start.bat", "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("title Servidor de Minecraft Optimizado\n")
        f.write(f'java {aikar_flags} -jar "{jar_name}" nogui\n')
        f.write("pause\n")

    with open("start.sh", "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write(f'java {aikar_flags} -jar "{jar_name}" nogui\n')

    # Dar permisos de ejecución al script de Linux
    if platform.system() != 'Windows':
        try:
            os.chmod("start.sh", 0o755)
        except Exception:
            pass
            
    print("[+] Scripts de inicio (start.bat / start.sh) actualizados.")

    # 5. Optimizar server.properties (Reducir lag por entidades, chunks y red)
    if os.path.exists("server.properties"):
        print("\n[*] Optimizando opciones dentro de server.properties...")
        with open("server.properties", "r") as f:
            lines = f.readlines()
            
        opts = {
            "view-distance": "view-distance=8\n",  # Distancia visual moderada (default es 10, que es muy pesado)
            "simulation-distance": "simulation-distance=4\n", # Menos simulación lejana = Mucho menos lag
            "network-compression-threshold": "network-compression-threshold=256\n", # Comprimir paquetes
            "max-tick-time": "max-tick-time=60000\n", # Previene que el servidor crashee si hay lag
            "entity-broadcast-range-percentage": "entity-broadcast-range-percentage=50\n" # Menos info de entidades lejanas
        }
        
        for k, v in opts.items():
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{k}="):
                    lines[i] = v
                    found = True
                    break
            if not found:
                lines.append(v)
                
        with open("server.properties", "w") as f:
            f.writelines(lines)
            
        print("[+] Archivo server.properties modificado con éxito.")
    else:
        print("\n[-] No se ha encontrado server.properties. (Arranca el servidor una vez para generarlo y luego vuelve a ejecutar este script).")

    print("\n" + "="*50)
    print("  ¡OPTIMIZACIÓN COMPLETADA CON ÉXITO!  ")
    print("="*50)
    print("Resumen de cambios aplicados:")
    print(f" > Memoria RAM Ajustada: {allocated_ram} GB.")
    print(" > Argumentos Java: Se han inyectado los Aikar's Flags (Mejor GC de Java).")
    print(" > Archivos de arranque: start.bat y start.sh ahora tienen el comando óptimo.")
    print(" > TPS y Lag: Se redujeron distancias de simulación si se detectó el archivo de propiedades.")
    print("\n¡Tu servidor está ahora en su máximo rendimiento!\n")
    
    input("Presiona ENTER para salir...")

if __name__ == "__main__":
    main()
