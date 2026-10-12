"""
Recordatorio de Pagos
Aplicación de escritorio para gestionar pagos pendientes y enviar recordatorios por correo.

Autor: Germain Aguilar
Versión: 2.0
"""

import smtplib
import os
import json
import re
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from typing import List, Tuple, Dict, Optional
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkcalendar import DateEntry
import webbrowser
import sv_ttk
import keyring
import keyring.errors


# ======================== CAPA DE DATOS ========================

class PasswordStore:
    """
    Guarda la contraseña de aplicación en el almacén de credenciales del
    sistema operativo (Administrador de credenciales de Windows, Llavero de
    macOS o Secret Service en Linux). La contraseña nunca se escribe en el
    archivo de configuración.
    """

    SERVICE = "RecordatorioPagos"

    @staticmethod
    def get(email: str) -> str:
        """Retorna la contraseña guardada para ese correo, o cadena vacía."""
        if not email:
            return ""
        try:
            return keyring.get_password(PasswordStore.SERVICE, email) or ""
        except keyring.errors.KeyringError as e:
            print(f"No se pudo leer la contraseña del almacén del sistema: {e}")
            return ""

    @staticmethod
    def set(email: str, password: str) -> bool:
        """Guarda la contraseña. Retorna False si el sistema no lo permite."""
        if not email or not password:
            return False
        try:
            keyring.set_password(PasswordStore.SERVICE, email, password)
            return True
        except keyring.errors.KeyringError as e:
            print(f"No se pudo guardar la contraseña en el almacén del sistema: {e}")
            return False

    @staticmethod
    def delete(email: str) -> None:
        """Elimina la contraseña guardada para ese correo, si existe."""
        if not email:
            return
        try:
            keyring.delete_password(PasswordStore.SERVICE, email)
        except keyring.errors.KeyringError:
            pass  # No había contraseña guardada o el almacén no está disponible


class DataManager:
    """Gestiona la persistencia y manipulación de datos de servicios."""

    def __init__(self, config_file: str = "payment_reminder_config.json"):
        """
        Inicializa el gestor de datos.

        Args:
            config_file: Ruta del archivo de configuración JSON
        """
        self.config_file = config_file
        self.servicios: List[Tuple[str, str, str]] = []
        self.config: Dict = {}
        # Correo con el que se guardó la contraseña la última vez
        self._email_guardado: str = ""

    def load_config(self) -> Dict:
        """
        Carga la configuración desde el archivo JSON. La contraseña se lee
        del almacén de credenciales del sistema, no del archivo.

        Returns:
            Diccionario con la configuración cargada
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                self.servicios = self.config.get("servicios", [])
                email = self.config.get("email_emisor", "")
                pendiente = self._migrate_plaintext_password(email)
                self._email_guardado = email
                self.config["password"] = pendiente or PasswordStore.get(email)
                return self.config
            else:
                return self._get_default_config()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar configuración: {e}")
            return self._get_default_config()

    def _migrate_plaintext_password(self, email: str) -> str:
        """
        Las versiones anteriores guardaban la contraseña en el JSON. Si queda
        una ahí, se pasa al almacén del sistema y se borra del archivo.

        Returns:
            La contraseña antigua si no se pudo mover al almacén (para seguir
            usándola en esta sesión), o cadena vacía en cualquier otro caso
        """
        antigua = self.config.pop("password", "")
        if not antigua:
            return ""
        if not PasswordStore.set(email, antigua):
            # No se pudo mover: se deja el archivo como estaba para no perderla
            return antigua
        self._write_config_file()
        return ""

    def _write_config_file(self) -> bool:
        """Escribe la configuración en disco, siempre sin la contraseña."""
        datos = {k: v for k, v in self.config.items() if k != "password"}
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error al guardar configuración: {e}")
            return False

    def _get_default_config(self) -> Dict:
        """Retorna la configuración por defecto."""
        return {
            "servicios": [],
            "email_emisor": "",
            "password": "",
            "email_receptor": "",
            "theme": "dark"
        }
    
    def save_config(self, email_emisor: str, password: str, 
                   email_receptor: str, theme: str) -> bool:
        """
        Guarda la configuración en el archivo JSON y la contraseña en el
        almacén de credenciales del sistema.

        Args:
            email_emisor: Correo del emisor
            password: Contraseña de aplicación
            email_receptor: Correo del receptor
            theme: Tema actual (light/dark)

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        self.config = {
            "servicios": self.servicios,
            "email_emisor": email_emisor,
            "password": password,
            "email_receptor": email_receptor,
            "theme": theme
        }

        # Si cambió el correo emisor, la contraseña del anterior ya no sirve
        if self._email_guardado and self._email_guardado != email_emisor:
            PasswordStore.delete(self._email_guardado)

        if password:
            PasswordStore.set(email_emisor, password)
        else:
            PasswordStore.delete(email_emisor)
        self._email_guardado = email_emisor

        return self._write_config_file()
    
    def add_servicio(self, nombre: str, fecha: str, monto: str) -> bool:
        """
        Agrega un nuevo servicio a la lista.
        
        Args:
            nombre: Nombre del servicio
            fecha: Fecha límite en formato YYYY-MM-DD
            monto: Monto del servicio
            
        Returns:
            True si se agregó correctamente
        """
        if not nombre.strip():
            return False
        
        self.servicios.append((nombre.strip(), fecha, monto.strip()))
        return True
    
    def remove_servicio(self, index: int) -> Optional[Tuple[str, str, str]]:
        """
        Elimina un servicio por su índice.
        
        Args:
            index: Índice del servicio a eliminar
            
        Returns:
            Tupla del servicio eliminado o None si el índice es inválido
        """
        if 0 <= index < len(self.servicios):
            return self.servicios.pop(index)
        return None
    
    def clear_servicios(self) -> int:
        """
        Elimina todos los servicios.
        
        Returns:
            Cantidad de servicios eliminados
        """
        count = len(self.servicios)
        self.servicios = []
        return count
    
    def get_servicios(self) -> List[Tuple[str, str, str]]:
        """Retorna la lista de servicios."""
        return self.servicios.copy()


# ======================== CAPA DE SERVICIOS ========================

class EmailService:
    """Gestiona el envío de correos electrónicos mediante SMTP."""
    
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Valida el formato de un correo electrónico.
        
        Args:
            email: Dirección de correo a validar
            
        Returns:
            True si el formato es válido
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def test_connection(email: str, password: str) -> Tuple[bool, str]:
        """
        Prueba la conexión SMTP con las credenciales proporcionadas.
        
        Args:
            email: Correo del emisor
            password: Contraseña de aplicación
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            server = smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT)
            server.starttls()
            server.login(email, password)
            server.quit()
            return True, "Conexión exitosa"
        except smtplib.SMTPAuthenticationError:
            return False, "Error de autenticación. Verifique su contraseña de aplicación."
        except smtplib.SMTPException as e:
            return False, f"Error SMTP: {str(e)}"
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"
    
    @staticmethod
    def send_email(emisor: str, password: str, receptor: str, 
                   asunto: str, cuerpo: str) -> Tuple[bool, str]:
        """
        Envía un correo electrónico.
        
        Args:
            emisor: Correo del emisor
            password: Contraseña de aplicación
            receptor: Correo del receptor
            asunto: Asunto del correo
            cuerpo: Cuerpo del mensaje
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = emisor
            msg['To'] = receptor
            msg['Subject'] = asunto
            msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT)
            server.starttls()
            server.login(emisor, password)
            server.sendmail(emisor, receptor, msg.as_string())
            server.quit()
            
            return True, f"Correo enviado exitosamente a {receptor}"
        except Exception as e:
            return False, f"Error al enviar correo: {str(e)}"


class ReminderGenerator:
    """Genera recordatorios formateados a partir de servicios."""
    
    @staticmethod
    def generate_reminder(servicios: List[Tuple[str, str, str]]) -> str:
        """
        Genera el texto del recordatorio.
        
        Args:
            servicios: Lista de tuplas (nombre, fecha, monto)
            
        Returns:
            Texto formateado del recordatorio
        """
        if not servicios:
            return "✅ No hay pagos pendientes registrados."
        
        hoy = datetime.date.today()
        mensaje = "📅 RECORDATORIO DE PAGOS PENDIENTES\n\n"
        mensaje += "=" * 50 + "\n\n"
        total_pendiente = 0.0
        
        for servicio, fecha_str, monto in servicios:
            try:
                fecha_limite = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                dias_restantes = (fecha_limite - hoy).days
                
                # Determinar estado y emoji
                if dias_restantes < 0:
                    estado = f"VENCIDO HACE {-dias_restantes} DÍAS"
                    estado_color = "🔴"
                elif dias_restantes == 0:
                    estado = "VENCE HOY"
                    estado_color = "🟠"
                elif dias_restantes <= 3:
                    estado = f"URGENTE ({dias_restantes} días)"
                    estado_color = "🟠"
                else:
                    estado = f"{dias_restantes} días restantes"
                    estado_color = "🟢"
                
                # Formatear monto
                try:
                    monto_val = float(monto) if monto else 0.0
                    formatted_monto = f"${monto_val:,.2f}"
                    total_pendiente += monto_val
                except ValueError:
                    formatted_monto = "No especificado"
                
                mensaje += f"• {servicio.upper()}:\n"
                mensaje += f"  Fecha límite: {fecha_limite.strftime('%d/%m/%Y')} ({estado_color} {estado})\n"
                mensaje += f"  Monto: {formatted_monto}\n\n"
                
            except ValueError:
                mensaje += f"• {servicio.upper()}: Fecha inválida\n\n"
        
        mensaje += "=" * 50 + "\n"
        mensaje += f"TOTAL PENDIENTE: ${total_pendiente:,.2f}\n"
        mensaje += "=" * 50 + "\n\n"
        mensaje += "Por favor realice los pagos a tiempo para evitar recargos.\n"
        mensaje += f"\nGenerado el: {hoy.strftime('%d/%m/%Y')}"
        
        return mensaje


# ======================== CAPA DE PRESENTACIÓN ========================

class ModernRecordatorioApp(tk.Tk):
    """Aplicación principal con interfaz gráfica moderna."""
    
    def __init__(self):
        super().__init__()
        
        # Configuración de ventana
        self.title("Recordatorio de Pagos Pro v2.0")
        self.geometry("900x800")
        self.resizable(True, True)
        
        # Configuración de fuentes
        self.fonts = {
            'title': ("Segoe UI", 16, "bold"),
            'section': ("Segoe UI", 11, "bold"),
            'label': ("Segoe UI", 9),
            'button': ("Segoe UI", 9, "bold"),
            'log': ("Consolas", 9)
        }
        
        # Colores
        self.colors = {
            'primary': "#4e73df",
            'secondary': "#858796",
            'success': "#1cc88a",
            'danger': "#e74a3b",
            'warning': "#f6c23e"
        }
        
        # Iconos
        self.icons = {
            'email': "✉️",
            'password': "🔑",
            'service': "📋",
            'calendar': "📅",
            'money': "💰",
            'delete': "🗑️",
            'send': "📤",
            'save': "💾",
            'refresh': "🔄",
            'test': "🔧"
        }
        
        # Inicializar servicios
        self.data_manager = DataManager()
        self.email_service = EmailService()
        self.reminder_generator = ReminderGenerator()
        
        # Cargar configuración
        config = self.data_manager.load_config()
        self.current_theme = config.get("theme", "dark")
        
        # Variables de UI
        self.email_emisor = tk.StringVar(value=config.get("email_emisor", ""))
        self.password = tk.StringVar(value=config.get("password", ""))
        self.email_receptor = tk.StringVar(value=config.get("email_receptor", ""))
        self.status_var = tk.StringVar(value="Listo")
        
        # Aplicar tema
        sv_ttk.set_theme(self.current_theme)
        
        # Crear interfaz
        self._create_menu()
        self._create_main_interface()
        
        # Validaciones iniciales
        self._validate_all_fields()
        self.log("✅ Aplicación iniciada correctamente")
        self.log(f"📊 Servicios cargados: {len(self.data_manager.servicios)}")
        self.log(f"🎨 Tema actual: {self.current_theme}")
    
    # ==================== CREACIÓN DE INTERFAZ ====================
    
    def _create_menu(self):
        """Crea la barra de menú."""
        menubar = tk.Menu(self)
        
        # Menú de opciones
        options_menu = tk.Menu(menubar, tearoff=0)
        options_menu.add_command(label="🌞 Tema Claro", command=lambda: self._change_theme("light"))
        options_menu.add_command(label="🌙 Tema Oscuro", command=lambda: self._change_theme("dark"))
        options_menu.add_separator()
        options_menu.add_command(label="ℹ️ Acerca de", command=self._show_about)
        
        menubar.add_cascade(label="Opciones", menu=options_menu)
        self.config(menu=menubar)
    
    def _create_main_interface(self):
        """Crea la interfaz principal."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        self._create_header(main_frame)
        
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Crear pestañas
        self._create_config_tab()
        self._create_services_tab()
        self._create_reminder_tab()
        
        # Barra de estado
        status_bar = ttk.Label(self, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_header(self, parent):
        """Crea el encabezado de la aplicación."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="💼 RECORDATORIO DE PAGOS PRO", 
                 font=self.fonts['title'], 
                 foreground=self.colors['primary']).pack()
        
        ttk.Label(header_frame, 
                 text="Gestiona tus pagos pendientes de forma profesional",
                 font=("Segoe UI", 10), 
                 foreground=self.colors['secondary']).pack()
    
    def _create_config_tab(self):
        """Crea la pestaña de configuración."""
        config_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(config_tab, text=f"{self.icons['email']} Configuración")
        
        # Frame principal de configuración
        config_frame = ttk.LabelFrame(config_tab, text="Configuración de Correo Electrónico", 
                                     padding=15)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Correo emisor
        self._create_email_field(config_frame, "Correo Emisor (Gmail):", 
                                self.email_emisor, "emisor", 0)
        
        # Contraseña
        self._create_password_field(config_frame, "Contraseña de Aplicación:", 
                                   self.password, 1)
        
        # Correo receptor
        self._create_email_field(config_frame, "Correo Receptor:", 
                                self.email_receptor, "receptor", 2)
        
        # Ayuda
        self._create_help_section(config_frame)
        
        # Botón de prueba
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        ttk.Button(btn_frame, text=f"{self.icons['test']} Probar Configuración", 
                  command=self._test_email_config,
                  style="Accent.TButton").pack()
    
    def _create_email_field(self, parent, label_text, variable, field_type, row):
        """Crea un campo de email con validación."""
        ttk.Label(parent, text=f"{self.icons['email']} {label_text}", 
                 font=self.fonts['label']).grid(row=row, column=0, sticky=tk.W, pady=10, padx=5)
        
        entry = ttk.Entry(parent, textvariable=variable, width=40)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=10, padx=5)
        
        status_label = ttk.Label(parent, text="✗", foreground=self.colors['danger'])
        status_label.grid(row=row, column=2, padx=5)
        
        # Guardar referencia al label de estado
        setattr(self, f"{field_type}_status", status_label)
        
        # Vincular validación
        variable.trace("w", lambda *args: self._validate_email(field_type))
        
        parent.columnconfigure(1, weight=1)
    
    def _create_password_field(self, parent, label_text, variable, row):
        """Crea un campo de contraseña con validación."""
        ttk.Label(parent, text=f"{self.icons['password']} {label_text}", 
                 font=self.fonts['label']).grid(row=row, column=0, sticky=tk.W, pady=10, padx=5)
        
        entry = ttk.Entry(parent, textvariable=variable, show="●", width=40)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=10, padx=5)
        
        self.password_status = ttk.Label(parent, text="✗", foreground=self.colors['danger'])
        self.password_status.grid(row=row, column=2, padx=5)
        
        variable.trace("w", lambda *args: self._validate_password())
    
    def _create_help_section(self, parent):
        """Crea la sección de ayuda."""
        help_frame = ttk.Frame(parent)
        help_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        help_link = ttk.Label(help_frame, 
                             text="❓ ¿Cómo obtener una contraseña de aplicación?", 
                             foreground=self.colors['primary'], 
                             cursor="hand2", 
                             font=self.fonts['label'])
        help_link.pack()
        help_link.bind("<Button-1>", lambda e: self._open_help_link())
    
    def _create_services_tab(self):
        """Crea la pestaña de servicios."""
        services_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(services_tab, text=f"{self.icons['service']} Servicios")
        
        # Frame para agregar servicios
        add_frame = ttk.LabelFrame(services_tab, text="Agregar Nuevo Servicio", padding=15)
        add_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Nombre del servicio
        ttk.Label(add_frame, text=f"{self.icons['service']} Nombre del Servicio:", 
                 font=self.fonts['label']).grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        
        self.servicio_name = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.servicio_name, width=50).grid(
            row=0, column=1, columnspan=2, sticky=tk.EW, pady=5, padx=5)
        
        # Fecha límite
        ttk.Label(add_frame, text=f"{self.icons['calendar']} Fecha Límite:", 
                 font=self.fonts['label']).grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        
        self.fecha_entry = DateEntry(add_frame, width=15, background='white',
                                     foreground='black', borderwidth=1,
                                     date_pattern='yyyy-mm-dd')
        self.fecha_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Monto
        ttk.Label(add_frame, text=f"{self.icons['money']} Monto:", 
                 font=self.fonts['label']).grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        
        self.monto = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.monto, width=15).grid(
            row=1, column=3, sticky=tk.W, pady=5, padx=5)
        
        # Botón agregar
        ttk.Button(add_frame, text="➕ Agregar Servicio", 
                  command=self._add_servicio,
                  style="Accent.TButton").grid(row=2, column=0, columnspan=4, pady=10)
        
        add_frame.columnconfigure(1, weight=1)
        
        # Frame para lista de servicios
        list_frame = ttk.LabelFrame(services_tab, text="Servicios Registrados", padding=15)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Treeview
        self._create_services_treeview(list_frame)
        
        # Botones de acción
        self._create_services_buttons(list_frame)
    
    def _create_services_treeview(self, parent):
        """Crea el Treeview para mostrar servicios."""
        columns = ("Servicio", "Fecha", "Monto", "Estado")
        self.servicios_tree = ttk.Treeview(parent, columns=columns, 
                                          show="headings", height=10,
                                          selectmode="browse")
        
        # Configurar columnas
        self.servicios_tree.heading("Servicio", text="Servicio", anchor=tk.W)
        self.servicios_tree.heading("Fecha", text="Fecha Límite", anchor=tk.CENTER)
        self.servicios_tree.heading("Monto", text="Monto", anchor=tk.CENTER)
        self.servicios_tree.heading("Estado", text="Estado", anchor=tk.CENTER)
        
        self.servicios_tree.column("Servicio", width=250, anchor=tk.W)
        self.servicios_tree.column("Fecha", width=120, anchor=tk.CENTER)
        self.servicios_tree.column("Monto", width=100, anchor=tk.CENTER)
        self.servicios_tree.column("Estado", width=150, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", 
                                 command=self.servicios_tree.yview)
        self.servicios_tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        self.servicios_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar servicios existentes
        self._update_services_list()
    
    def _create_services_buttons(self, parent):
        """Crea los botones de acción para servicios."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text=f"{self.icons['delete']} Eliminar Seleccionado", 
                  command=self._delete_servicio).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text=f"{self.icons['delete']} Limpiar Todos", 
                  command=self._clear_servicios).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text=f"{self.icons['refresh']} Actualizar", 
                  command=self._update_services_list).pack(side=tk.RIGHT, padx=5)
    
    def _create_reminder_tab(self):
        """Crea la pestaña de recordatorio."""
        reminder_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(reminder_tab, text="📋 Recordatorio")
        
        # Frame para el recordatorio
        reminder_frame = ttk.LabelFrame(reminder_tab, text="Vista Previa del Recordatorio", 
                                       padding=15)
        reminder_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Área de texto
        text_bg = "#1a1a1a" if self.current_theme == "dark" else "white"
        text_fg = "white" if self.current_theme == "dark" else "black"
        
        self.text_area = scrolledtext.ScrolledText(reminder_frame, width=70, height=15,
                                                   font=("Segoe UI", 10), wrap=tk.WORD,
                                                   bg=text_bg, fg=text_fg,
                                                   padx=10, pady=10)
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.text_area.configure(state='disabled')
        
        # Botones
        btn_frame = ttk.Frame(reminder_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="🔄 Generar Recordatorio", 
                  command=self._show_reminder,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text=f"{self.icons['send']} Enviar por Email", 
                  command=self._send_reminder).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text=f"{self.icons['save']} Guardar como TXT", 
                  command=self._save_reminder).pack(side=tk.LEFT, padx=5)
        
        # Frame para el log
        log_frame = ttk.LabelFrame(reminder_tab, text="Registro de Actividad", padding=15)
        log_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 10))
        
        log_bg = "#1a1a1a" if self.current_theme == "dark" else "#ecf0f1"
        log_fg = "#1cc88a" if self.current_theme == "dark" else "#27ae60"
        
        self.log_area = scrolledtext.ScrolledText(log_frame, width=70, height=8,
                                                  font=self.fonts['log'],
                                                  foreground=log_fg, bg=log_bg,
                                                  padx=10, pady=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled')
        
        ttk.Button(log_frame, text="🗑️ Limpiar Registro", 
                  command=self._clear_log).pack(side=tk.RIGHT, pady=(5, 0))
    
    # ==================== VALIDACIONES ====================
    
    def _validate_email(self, field_type: str) -> bool:
        """Valida un campo de email."""
        email = self.email_emisor.get() if field_type == "emisor" else self.email_receptor.get()
        status_label = getattr(self, f"{field_type}_status")
        
        if self.email_service.validate_email(email):
            status_label.config(text="✓", foreground=self.colors['success'])
            return True
        else:
            status_label.config(text="✗", foreground=self.colors['danger'])
            return False
    
    def _validate_password(self) -> bool:
        """Valida el campo de contraseña."""
        if len(self.password.get()) > 0:
            self.password_status.config(text="✓", foreground=self.colors['success'])
            return True
        else:
            self.password_status.config(text="✗", foreground=self.colors['danger'])
            return False
    
    def _validate_all_fields(self):
        """Valida todos los campos."""
        self._validate_email("emisor")
        self._validate_email("receptor")
        self._validate_password()
    
    # ==================== GESTIÓN DE SERVICIOS ====================
    
    def _add_servicio(self):
        """Agrega un nuevo servicio."""
        nombre = self.servicio_name.get().strip()
        fecha = self.fecha_entry.get_date().strftime("%Y-%m-%d")
        monto = self.monto.get().strip()
        
        if not nombre:
            messagebox.showwarning("Entrada Inválida", 
                                  "Por favor ingrese el nombre del servicio.")
            return
        
        # Validar monto
        if monto:
            try:
                float(monto)
            except ValueError:
                messagebox.showwarning("Monto Inválido", 
                                      "El monto debe ser un valor numérico.")
                return
        
        # Agregar servicio
        if self.data_manager.add_servicio(nombre, fecha, monto):
            self._update_services_list()
            self.servicio_name.set("")
            self.monto.set("")
            self.log(f"✅ Servicio agregado: {nombre} - {fecha} - ${monto or '0.00'}")
            self.status_var.set(f"Servicio '{nombre}' agregado correctamente")
            self._save_config()
            
            # Auto-generar recordatorio
            self._show_reminder()
        else:
            messagebox.showerror("Error", "No se pudo agregar el servicio.")
    
    def _update_services_list(self):
        """Actualiza la lista de servicios en el Treeview."""
        # Limpiar items existentes
        for item in self.servicios_tree.get_children():
            self.servicios_tree.delete(item)
        
        # Configurar tags
        self.servicios_tree.tag_configure('vencido', foreground=self.colors['danger'])
        self.servicios_tree.tag_configure('urgente', foreground=self.colors['warning'])
        self.servicios_tree.tag_configure('normal', foreground=self.colors['success'])
        
        # Añadir servicios
        hoy = datetime.date.today()
        for servicio, fecha, monto in self.data_manager.get_servicios():
            try:
                fecha_limite = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
                dias_restantes = (fecha_limite - hoy).days
                
                # Determinar estado y tag
                if dias_restantes < 0:
                    estado = f"🔴 Vencido ({-dias_restantes}d)"
                    tag = 'vencido'
                elif dias_restantes == 0:
                    estado = "🟠 Vence hoy"
                    tag = 'urgente'
                elif dias_restantes <= 3:
                    estado = f"🟠 Urgente ({dias_restantes}d)"
                    tag = 'urgente'
                else:
                    estado = f"🟢 {dias_restantes} días"
                    tag = 'normal'
                
                # Formatear monto
                try:
                    monto_val = float(monto) if monto else 0.0
                    formatted_monto = f"${monto_val:,.2f}"
                except ValueError:
                    formatted_monto = "$0.00"
                
                # Insertar en el Treeview
                self.servicios_tree.insert("", "end", 
                                          values=(servicio, fecha, formatted_monto, estado),
                                          tags=(tag,))
            except ValueError:
                # Fecha inválida
                self.servicios_tree.insert("", "end", 
                                          values=(servicio, fecha, monto, "⚠️ Fecha inválida"),
                                          tags=('vencido',))
    
    def _delete_servicio(self):
        """Elimina el servicio seleccionado."""
        seleccion = self.servicios_tree.selection()
        if not seleccion:
            messagebox.showwarning("Seleccionar Servicio", 
                                  "Por favor seleccione un servicio para eliminar.")
            return
        
        item = seleccion[0]
        idx = self.servicios_tree.index(item)
        eliminado = self.data_manager.remove_servicio(idx)
        
        if eliminado:
            self._update_services_list()
            self.log(f"🗑️ Servicio eliminado: {eliminado[0]}")
            self.status_var.set(f"Servicio '{eliminado[0]}' eliminado")
            self._save_config()
            self._show_reminder()
    
    def _clear_servicios(self):
        """Limpia todos los servicios."""
        if not self.data_manager.servicios:
            messagebox.showinfo("Sin Servicios", "No hay servicios para eliminar.")
            return
        
        if messagebox.askyesno("Confirmar", 
                              "¿Está seguro que desea eliminar TODOS los servicios?"):
            count = self.data_manager.clear_servicios()
            self._update_services_list()
            self.log(f"🗑️ Eliminados {count} servicios")
            self.status_var.set("Todos los servicios han sido eliminados")
            self._save_config()
            self._show_reminder()
    
    # ==================== RECORDATORIO ====================
    
    def _show_reminder(self):
        """Muestra el recordatorio generado."""
        texto = self.reminder_generator.generate_reminder(
            self.data_manager.get_servicios())
        
        self.text_area.configure(state='normal')
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert(tk.END, texto)
        self.text_area.configure(state='disabled')
        
        self.log("📋 Recordatorio generado")
        self.status_var.set("Recordatorio generado correctamente")
    
    def _send_reminder(self):
        """Envía el recordatorio por correo."""
        if not self.data_manager.servicios:
            messagebox.showinfo("Sin Servicios", 
                               "No hay servicios registrados para enviar.")
            return
        
        # Validar configuración
        if not (self._validate_email("emisor") and 
                self._validate_email("receptor") and 
                self._validate_password()):
            messagebox.showwarning("Configuración Incompleta", 
                                  "Por favor complete la configuración de correo.")
            return
        
        emisor = self.email_emisor.get().strip()
        pwd = self.password.get()
        receptor = self.email_receptor.get().strip()
        asunto = "Recordatorio de Pagos Pendientes"
        cuerpo = self.reminder_generator.generate_reminder(
            self.data_manager.get_servicios())
        
        # Diálogo de progreso
        progress_dialog = tk.Toplevel(self)
        progress_dialog.title("Enviando correo...")
        progress_dialog.geometry("350x120")
        progress_dialog.resizable(False, False)
        progress_dialog.grab_set()
        
        ttk.Label(progress_dialog, 
                 text="📤 Enviando recordatorio, por favor espere...",
                 font=self.fonts['label']).pack(pady=15)
        
        progress_bar = ttk.Progressbar(progress_dialog, mode="indeterminate")
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start()
        
        # Enviar en hilo separado
        def send_thread():
            success, message = self.email_service.send_email(
                emisor, pwd, receptor, asunto, cuerpo)
            
            progress_dialog.destroy()
            
            if success:
                self.log(f"✅ {message}")
                self.status_var.set(message)
                messagebox.showinfo("Correo Enviado", message)
            else:
                self.log(f"❌ {message}")
                self.status_var.set("Error al enviar correo")
                messagebox.showerror("Error de Envío", message)
            
            self._save_config()
        
        threading.Thread(target=send_thread, daemon=True).start()
    
    def _save_reminder(self):
        """Guarda el recordatorio como archivo TXT."""
        if not self.data_manager.servicios:
            messagebox.showinfo("Sin Contenido", "No hay recordatorio para guardar.")
            return
        
        texto = self.text_area.get("1.0", tk.END)
        try:
            filename = f"recordatorio_pagos_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(texto)
            
            self.log(f"💾 Recordatorio guardado: {filename}")
            self.status_var.set(f"Archivo guardado: {filename}")
            messagebox.showinfo("Guardado Exitoso", 
                               f"Recordatorio guardado en:\n{filename}")
        except Exception as e:
            self.log(f"❌ Error al guardar: {str(e)}")
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")
    
    # ==================== EMAIL ====================
    
    def _test_email_config(self):
        """Prueba la configuración de correo."""
        if not (self._validate_email("emisor") and self._validate_password()):
            messagebox.showwarning("Configuración Incompleta", 
                                  "Complete el correo emisor y la contraseña.")
            return
        
        emisor = self.email_emisor.get().strip()
        pwd = self.password.get()
        
        self.log("🔧 Probando configuración de correo...")
        self.status_var.set("Probando conexión...")
        
        success, message = self.email_service.test_connection(emisor, pwd)
        
        if success:
            self.log(f"✅ {message}")
            self.status_var.set("Configuración válida")
            messagebox.showinfo("Prueba Exitosa", 
                               "✅ La configuración es válida.\nPuede enviar recordatorios.")
        else:
            self.log(f"❌ {message}")
            self.status_var.set("Error en configuración")
            messagebox.showerror("Error de Configuración", 
                                f"❌ {message}\n\nAsegúrese de usar una contraseña de aplicación.")
    
    # ==================== UTILIDADES ====================
    
    def _change_theme(self, theme_name: str):
        """Cambia el tema de la aplicación."""
        sv_ttk.set_theme(theme_name)
        self.current_theme = theme_name
        self.log(f"🎨 Tema cambiado a: {theme_name}")
        self._save_config()
        
        # Actualizar colores de áreas de texto
        if theme_name == "light":
            self.text_area.configure(bg="white", fg="black")
            self.log_area.configure(bg="#ecf0f1", fg="#27ae60")
        else:
            self.text_area.configure(bg="#1a1a1a", fg="white")
            self.log_area.configure(bg="#1a1a1a", fg="#1cc88a")
    
    def _show_about(self):
        """Muestra información sobre la aplicación."""
        about_text = """
        📋 Recordatorio de Pagos Pro v2.0
        
        Aplicación profesional para gestionar
        pagos pendientes y enviar recordatorios
        automáticos por correo electrónico.
        
        Características:
        • Gestión de servicios con fechas
        • Recordatorios automáticos
        • Envío por email (Gmail)
        • Temas claro/oscuro
        • Exportación a TXT
        
        © 2026 - Sistema de Recordatorios
        """
        messagebox.showinfo("Acerca de", about_text)
    
    def _open_help_link(self):
        """Abre el enlace de ayuda para contraseñas de aplicación."""
        webbrowser.open("https://support.google.com/accounts/answer/185833")
        self.log("🌐 Abierto enlace de ayuda para contraseñas de aplicación")
    
    def log(self, mensaje: str):
        """Añade una entrada al registro de actividad."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {mensaje}"
        
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, log_entry + "\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')
    
    def _clear_log(self):
        """Limpia el registro de actividad."""
        self.log_area.configure(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.configure(state='disabled')
        self.log("🗑️ Registro limpiado")
    
    def _save_config(self):
        """Guarda la configuración actual."""
        success = self.data_manager.save_config(
            self.email_emisor.get(),
            self.password.get(),
            self.email_receptor.get(),
            self.current_theme
        )
        
        if success:
            self.log("💾 Configuración guardada")
        else:
            self.log("❌ Error al guardar configuración")


# ======================== PUNTO DE ENTRADA ========================

if __name__ == "__main__":
    app = ModernRecordatorioApp()
    app.mainloop()
