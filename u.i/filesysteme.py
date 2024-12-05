import os

# Définir la structure du fichier système
structure = {
    "src": {
        "assets": {
            "images": {},
            "icons": {},
            "styles": {
                "index.css": ""
            }
        },
        "components": {
            "common": {
                "Button": {
                    "Button.jsx": "",
                    "Button.styles.js": ""
                },
                "Input": {},
                "Card": {},
                "Modal": {},
                "Alert": {},
                "Loading": {}
            },
            "auth": {
                "LoginForm": {
                    "index.jsx": "",
                    "LoginForm.jsx": "",
                    "LoginFormAdmin.jsx": "",
                    "LoginFormEmployee.jsx": "",
                    "TwoFactorForm.jsx": ""
                },
                "SignupForm": {
                    "index.jsx": "",
                    "SignupSteps": {
                        "PersonalInfo.jsx": "",
                        "ProfessionalInfo.jsx": "",
                        "EmergencyContact.jsx": "",
                        "Review.jsx": ""
                    },
                    "StepProgress.jsx": ""
                }
            },
            "dashboard": {
                "admin": {
                    "Overview": {},
                    "UserManagement": {},
                    "DepartmentControl": {},
                    "Reports": {}
                },
                "employee": {
                    "Profile": {},
                    "Attendance": {},
                    "Leaves": {},
                    "Notifications": {}
                }
            },
            "attendance": {
                "QRScanner": {},
                "NFCReader": {},
                "BreakTimer": {},
                "AttendanceStatus": {}
            }
        },
        "context": {
            "AuthContext.jsx": "",
            "ThemeContext.jsx": "",
            "AttendanceContext.jsx": ""
        },
        "hooks": {
            "useAuth.js": "",
            "useAttendance.js": "",
            "useNFC.js": "",
            "useQRCode.js": ""
        },
        "layouts": {
            "AuthLayout.jsx": "",
            "DashboardLayout.jsx": "",
            "AttendanceLayout.jsx": "",
            "PublicLayout.jsx": ""
        },
        "pages": {
            "auth": {
                "Login.jsx": "",
                "Signup.jsx": ""
            },
            "dashboard": {
                "admin": {
                    "AdminDashboard.jsx": "",
                    "UserManagement.jsx": "",
                    "Reports.jsx": ""
                },
                "employee": {
                    "EmployeeDashboard.jsx": "",
                    "Profile.jsx": ""
                }
            },
            "attendance": {
                "AttendanceTerminal.jsx": ""
            }
        },
        "services": {
            "api": {
                "auth.js": "",
                "users.js": "",
                "attendance.js": ""
            },
            "nfc": {
                "nfcHandler.js": ""
            },
            "qr": {
                "qrGenerator.js": ""
            }
        },
        "store": {
            "slices": {
                "authSlice.js": "",
                "attendanceSlice.js": ""
            },
            "store.js": ""
        },
        "theme": {
            "colors.js": "",
            "typography.js": "",
            "components.js": ""
        },
        "utils": {
            "validation.js": "",
            "formatters.js": "",
            "helpers.js": ""
        },
        "App.jsx": "",
        "main.jsx": "",
        "routes.jsx": ""
    }
}

# Fonction pour créer la structure de répertoires et de fichiers
def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            # Si le contenu est un dictionnaire, on crée un dossier
            os.makedirs(path, exist_ok=True)
            # On appelle récursivement pour créer le contenu à l'intérieur
            create_structure(path, content)
        else:
            # Si le contenu est une chaîne vide, on crée un fichier
            with open(path, 'w') as file:
                file.write(content)

# Créer la structure dans le répertoire de travail actuel
create_structure(".", structure)

print("Structure de fichiers créée avec succès !")
