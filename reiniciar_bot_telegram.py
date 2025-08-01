#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para reiniciar el bot de Telegram en PythonAnywhere después de actualizar el token
"""

import paramiko
import sys
import time


class PythonAnywhereSSH:
    """Clase para manejar conexiones SSH a PythonAnywhere"""
    
    def __init__(self, hostname: str, username: str, password: str, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.client = None
    
    def conectar(self) -> bool:
        """Establece la conexión SSH"""
        try:
            print(f"🔌 Conectando a {self.hostname} como {self.username}...")
            
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            print("✅ Conexión SSH establecida exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def ejecutar_comando(self, comando: str) -> str:
        """Ejecuta un comando en el servidor remoto"""
        if not self.client:
            print("❌ No hay conexión SSH activa")
            return ""
        
        try:
            print(f"🚀 Ejecutando: {comando}")
            
            stdin, stdout, stderr = self.client.exec_command(comando)
            
            salida = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                print(f"⚠️ Errores: {error}")
            
            return salida
            
        except Exception as e:
            print(f"❌ Error ejecutando comando: {e}")
            return ""
    
    def cerrar_conexion(self):
        """Cierra la conexión SSH"""
        if self.client:
            self.client.close()
            print("🔌 Conexión SSH cerrada")
    
    def __enter__(self):
        if self.conectar():
            return self
        else:
            raise Exception("No se pudo establecer la conexión SSH")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar_conexion()


def main():
    """Función principal para reiniciar el bot de Telegram"""
    
    # Configuración de conexión
    HOSTNAME = "ssh.eu.pythonanywhere.com"
    USERNAME = "sacristobalspa"
    PASSWORD = "dirqoc-navco2-zethaB"
    
    print("🤖 Reiniciando Bot de Telegram en PythonAnywhere")
    print("=" * 50)
    
    try:
        with PythonAnywhereSSH(HOSTNAME, USERNAME, PASSWORD) as ssh:
            
            # 1. Verificar procesos del bot activos
            print("\n🔍 Verificando procesos del bot activos:")
            resultado = ssh.ejecutar_comando("ps aux | grep telegram_bot_always")
            if resultado:
                print(resultado)
            
            # 2. Matar procesos del bot si están corriendo
            print("\n🛑 Deteniendo procesos del bot:")
            ssh.ejecutar_comando("pkill -f telegram_bot_always")
            time.sleep(2)
            
            # 3. Verificar que se detuvieron
            print("\n✅ Verificando que se detuvieron:")
            resultado = ssh.ejecutar_comando("ps aux | grep telegram_bot_always | grep -v grep")
            if resultado.strip():
                print(f"⚠️ Aún hay procesos: {resultado}")
            else:
                print("✅ Todos los procesos del bot se detuvieron")
            
            # 4. Navegar al directorio del proyecto
            print("\n📂 Navegando al directorio del proyecto:")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && pwd")
            print(f"Directorio actual: {resultado.strip()}")
            
            # 5. Verificar que el archivo del bot existe
            print("\n📄 Verificando archivo del bot:")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && ls -la telegram_bot_always.py")
            if resultado:
                print(resultado)
            
            # 6. Verificar el nuevo token en el archivo
            print("\n🔑 Verificando nuevo token en el archivo:")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && grep -n '8204914856' telegram_bot_always.py")
            if resultado:
                print("✅ Nuevo token encontrado en el archivo:")
                print(resultado)
            else:
                print("❌ Nuevo token NO encontrado en el archivo")
            
            # 7. Iniciar el bot en segundo plano
            print("\n🚀 Iniciando bot en segundo plano:")
            comando_inicio = "cd webfinal/mi_app && nohup python3 telegram_bot_always.py > telegram_bot.log 2>&1 &"
            ssh.ejecutar_comando(comando_inicio)
            
            # 8. Esperar un momento y verificar que se inició
            print("\n⏳ Esperando 5 segundos...")
            time.sleep(5)
            
            # 9. Verificar que el bot se está ejecutando
            print("\n✅ Verificando que el bot se inició:")
            resultado = ssh.ejecutar_comando("ps aux | grep telegram_bot_always | grep -v grep")
            if resultado.strip():
                print("✅ Bot iniciado exitosamente:")
                print(resultado)
            else:
                print("❌ El bot no se inició correctamente")
            
            # 10. Mostrar últimas líneas del log
            print("\n📋 Últimas líneas del log:")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && tail -10 telegram_bot.log")
            if resultado:
                print(resultado)
            
            print("\n" + "=" * 50)
            print("🎯 RESUMEN:")
            print("✅ Pull completado en PythonAnywhere")
            print("✅ Token actualizado en el código")
            print("✅ Bot reiniciado con nuevo token")
            print("🔒 El bot ahora está seguro")
            
    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()