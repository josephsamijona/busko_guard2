from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator

class TimeStampedModel(models.Model):
    """Modèle abstrait pour ajouter created_at et updated_at"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Mis à jour le"))

    class Meta:
        abstract = True

# Modèle Department
class Department(TimeStampedModel):
    """Modèle pour les départements"""
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom du département")
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Code du département")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_("Responsable")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )

    class Meta:
        verbose_name = _("Département")
        verbose_name_plural = _("Départements")
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        super().clean()
        if self.code:
            self.code = self.code.upper()
            if not self.code.isalnum():
                raise ValidationError({
                    'code': _("Le code doit être alphanumérique (lettres et chiffres uniquement)")
                })
            if not self.code[0].isalpha():
                raise ValidationError({
                    'code': _("Le code doit commencer par une lettre")
                })
            if len(self.code) < 3:
                raise ValidationError({
                    'code': _("Le code doit contenir au moins 3 caractères")
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_active_users(self):
        """Retourne les utilisateurs actifs du département"""
        return self.user_profiles.filter(user__is_active=True)

    def get_stats(self):
        """Retourne les statistiques du département"""
        return {
            'total_employees': self.user_profiles.count(),
            'active_employees': self.get_active_users().count(),
            'created_at': self.created_at,
            'last_updated': self.updated_at
        }

# Modèle UserProfile
class UserProfile(TimeStampedModel):
    """Extension du modèle User de Django pour les informations supplémentaires"""

    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrateur')
        STAFF = 'STAFF', _('Personnel')
        SECURITY = 'SECURITY', _('Agent de sécurité')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("Utilisateur")
    )
    matricule = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Matricule")
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profiles',
        verbose_name=_("Département")
    )
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STAFF,
        verbose_name=_("Rôle")
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Numéro de téléphone")
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Adresse")
    )
    emergency_contact = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Contact d'urgence")
    )
    emergency_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Téléphone d'urgence")
    )

    class Meta:
        verbose_name = _("Profil utilisateur")
        verbose_name_plural = _("Profils utilisateurs")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.matricule})"

    def clean(self):
        super().clean()
        if self.phone_number and not self.phone_number.isdigit():
            raise ValidationError({
                'phone_number': _("Le numéro de téléphone ne doit contenir que des chiffres")
            })
        if self.emergency_phone and not self.emergency_phone.isdigit():
            raise ValidationError({
                'emergency_phone': _("Le numéro d'urgence ne doit contenir que des chiffres")
            })

    def save(self, *args, **kwargs):
        if not self.matricule:
            self.matricule = self.generate_matricule()
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_matricule():
        """Génère un matricule unique"""
        prefix = "BG"
        year = timezone.now().year
        last_profile = UserProfile.objects.filter(
            matricule__startswith=f"{prefix}{year}"
        ).order_by('matricule').last()

        if last_profile:
            last_number = int(last_profile.matricule[-4:])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}{year}{new_number:04d}"

# Modèle NFCCard
class NFCCard(TimeStampedModel):
    """Modèle pour gérer les cartes NFC"""

    class CardStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Actif')
        INACTIVE = 'INACTIVE', _('Inactif')
        LOST = 'LOST', _('Perdu')
        STOLEN = 'STOLEN', _('Volé')
        EXPIRED = 'EXPIRED', _('Expiré')
        DAMAGED = 'DAMAGED', _('Endommagé')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='nfc_card',
        verbose_name=_("Utilisateur")
    )
    card_uid = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("UID de la carte")
    )
    status = models.CharField(
        max_length=20,
        choices=CardStatus.choices,
        default=CardStatus.ACTIVE,
        verbose_name=_("Statut")
    )
    issue_date = models.DateField(
        default=timezone.now,
        verbose_name=_("Date d'émission")
    )
    expiry_date = models.DateField(
        verbose_name=_("Date d'expiration")
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernière utilisation")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    access_level = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Niveau d'accès")
    )
    security_hash = models.CharField(
        max_length=255,
        verbose_name=_("Hash de sécurité")
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )

    class Meta:
        verbose_name = _("Carte NFC")
        verbose_name_plural = _("Cartes NFC")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.card_uid} - {self.user.get_full_name()}"

    def clean(self):
        if self.expiry_date and self.expiry_date < timezone.now().date():
            raise ValidationError(_("La date d'expiration ne peut pas être dans le passé"))

# Modèle AttendanceRule
class AttendanceRule(TimeStampedModel):
    """Configuration des règles de présence"""
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom de la règle")
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='attendance_rules',
        verbose_name=_("Département")
    )
    start_time = models.TimeField(
        verbose_name=_("Heure de début")
    )
    end_time = models.TimeField(
        verbose_name=_("Heure de fin")
    )
    grace_period_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name=_("Période de grâce (minutes)")
    )
    minimum_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8.0,
        verbose_name=_("Heures minimum requises")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )

    class Meta:
        verbose_name = _("Règle de présence")
        verbose_name_plural = _("Règles de présence")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.department}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError(
                _("L'heure de début doit être antérieure à l'heure de fin")
            )

# Modèle AttendanceRecord
class AttendanceRecord(TimeStampedModel):
    """Enregistrement des présences"""

    class Status(models.TextChoices):
        ARRIVAL = 'ARRIVAL', _('Arrivée')
        DEPARTURE = 'DEPARTURE', _('Départ')
        PAUSE_START = 'PAUSE_START', _('Début de pause')
        PAUSE_END = 'PAUSE_END', _('Fin de pause')
        BREAK_START = 'BREAK_START', _('Début de break')
        BREAK_END = 'BREAK_END', _('Fin de break')
        TEMP_EXIT = 'TEMP_EXIT', _('Sortie temporaire')
        TEMP_RETURN = 'TEMP_RETURN', _('Retour temporaire')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name=_("Utilisateur")
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Horodatage")
    )
    action_type = models.CharField(
        max_length=20,
        choices=Status.choices,
        verbose_name=_("Type d'action")
    )
    location = models.ForeignKey(
        'AccessPoint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_records',
        verbose_name=_("Point d'accès")
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )

    class Meta:
        verbose_name = _("Enregistrement de présence")
        verbose_name_plural = _("Enregistrements de présence")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_action_type_display()} à {self.timestamp}"

# Modèle PresenceHistory
class PresenceHistory(TimeStampedModel):
    """Archive les modifications des enregistrements de présence pour audit"""

    attendance_record = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_("Enregistrement de présence")
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='modified_presences',
        verbose_name=_("Modifié par")
    )
    modified_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Modifié le")
    )
    previous_action_type = models.CharField(
        max_length=20,
        choices=AttendanceRecord.Status.choices,
        verbose_name=_("Type d'action précédent")
    )
    new_action_type = models.CharField(
        max_length=20,
        choices=AttendanceRecord.Status.choices,
        verbose_name=_("Nouveau type d'action")
    )
    reason = models.TextField(
        verbose_name=_("Raison de la modification")
    )

    def __str__(self):
        return f"Modification par {self.modified_by} sur {self.attendance_record}"

# Modèle Leave
class Leave(TimeStampedModel):
    """Gestion des congés et absences"""

    class LeaveType(models.TextChoices):
        VACATION = 'VACATION', _('Congés payés')
        SICK = 'SICK', _('Maladie')
        PERSONAL = 'PERSONAL', _('Personnel')
        OTHER = 'OTHER', _('Autre')

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('En attente')
        APPROVED = 'APPROVED', _('Approuvé')
        REJECTED = 'REJECTED', _('Rejeté')
        CANCELLED = 'CANCELLED', _('Annulé')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leaves',
        verbose_name=_("Utilisateur")
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LeaveType.choices,
        verbose_name=_("Type de congé")
    )
    start_date = models.DateField(
        verbose_name=_("Date de début")
    )
    end_date = models.DateField(
        verbose_name=_("Date de fin")
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Statut")
    )
    reason = models.TextField(
        verbose_name=_("Motif")
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_leaves',
        verbose_name=_("Approuvé par")
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'approbation")
    )
    comments = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Commentaires")
    )

    class Meta:
        verbose_name = _("Congé")
        verbose_name_plural = _("Congés")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_leave_type_display()} ({self.start_date})"

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError(
                _("La date de début doit être antérieure ou égale à la date de fin")
            )

# Modèle Notification
class Notification(TimeStampedModel):
    """Gère les notifications et alertes pour les utilisateurs ou administrateurs"""

    NOTIFICATION_TYPES = [
        ('missing_presence', 'Présence Manquante'),
        ('anomaly', 'Anomalie'),
        ('general', 'Général'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_("Destinataire")
    )
    message = models.TextField(
        verbose_name=_("Message")
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Lu")
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        verbose_name=_("Type de notification")
    )

    def __str__(self):
        return f"Notification à {self.recipient} - {self.notification_type}"

# Modèle LogEntry
class LogEntry(TimeStampedModel):
    """Enregistre les opérations effectuées dans le système pour traçabilité et sécurité"""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='log_entries',
        verbose_name=_("Utilisateur")
    )
    action = models.CharField(
        max_length=255,
        verbose_name=_("Action")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Horodatage")
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Adresse IP")
    )
    user_agent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Agent utilisateur")
    )

    def __str__(self):
        return f"Action par {self.user} à {self.timestamp}"

# Modèle Report
class Report(TimeStampedModel):
    """Modèle pour gérer les rapports"""

    class ReportType(models.TextChoices):
        ATTENDANCE = 'ATTENDANCE', _('Présence')
        SECURITY = 'SECURITY', _('Sécurité')
        DEPARTMENT = 'DEPARTMENT', _('Département')
        USER = 'USER', _('Utilisateur')
        CUSTOM = 'CUSTOM', _('Personnalisé')

    class ReportFormat(models.TextChoices):
        PDF = 'PDF', _('PDF')
        EXCEL = 'EXCEL', _('Excel')
        CSV = 'CSV', _('CSV')
        HTML = 'HTML', _('HTML')

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('En attente')
        PROCESSING = 'PROCESSING', _('En cours')
        COMPLETED = 'COMPLETED', _('Terminé')
        ERROR = 'ERROR', _('Erreur')

    name = models.CharField(
        max_length=255,
        verbose_name=_("Nom")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        verbose_name=_("Type de rapport")
    )
    format = models.CharField(
        max_length=20,
        choices=ReportFormat.choices,
        default=ReportFormat.PDF,
        verbose_name=_("Format")
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Statut")
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Paramètres")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports',
        verbose_name=_("Créé par")
    )
    file = models.FileField(
        upload_to='reports/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'xlsx', 'csv', 'html'])],
        verbose_name=_("Fichier")
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Message d'erreur")
    )
    generation_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_("Temps de génération")
    )

    class Meta:
        verbose_name = _("Rapport")
        verbose_name_plural = _("Rapports")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

# Modèle ReportSchedule
class ReportSchedule(TimeStampedModel):
    """Modèle pour gérer la planification des rapports"""

    class Frequency(models.TextChoices):
        DAILY = 'DAILY', _('Quotidien')
        WEEKLY = 'WEEKLY', _('Hebdomadaire')
        MONTHLY = 'MONTHLY', _('Mensuel')
        QUARTERLY = 'QUARTERLY', _('Trimestriel')

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_("Rapport")
    )
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        verbose_name=_("Fréquence")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    next_run = models.DateTimeField(
        verbose_name=_("Prochaine exécution")
    )
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernière exécution")
    )
    recipients = models.ManyToManyField(
        User,
        related_name='report_subscriptions',
        verbose_name=_("Destinataires")
    )
    send_empty = models.BooleanField(
        default=False,
        verbose_name=_("Envoyer si vide")
    )
    configuration = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Configuration")
    )

    class Meta:
        verbose_name = _("Planification de rapport")
        verbose_name_plural = _("Planifications de rapports")
        ordering = ['next_run']

    def __str__(self):
        return f"{self.report.name} - {self.get_frequency_display()}"

# Modèle NFCReader
class NFCReader(TimeStampedModel):
    """Modèle pour gérer les lecteurs NFC"""

    class ReaderStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Actif')
        INACTIVE = 'INACTIVE', _('Inactif')
        MAINTENANCE = 'MAINTENANCE', _('En maintenance')
        ERROR = 'ERROR', _('Erreur')

    class ReaderType(models.TextChoices):
        ENTRANCE = 'ENTRANCE', _('Entrée')
        EXIT = 'EXIT', _('Sortie')
        BOTH = 'BOTH', _('Entrée/Sortie')
        SPECIAL = 'SPECIAL', _('Spécial')

    identifier = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Identifiant")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    location = models.CharField(
        max_length=200,
        verbose_name=_("Emplacement")
    )
    reader_type = models.CharField(
        max_length=20,
        choices=ReaderType.choices,
        default=ReaderType.BOTH,
        verbose_name=_("Type de lecteur")
    )
    status = models.CharField(
        max_length=20,
        choices=ReaderStatus.choices,
        default=ReaderStatus.ACTIVE,
        verbose_name=_("Statut")
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Adresse IP")
    )
    last_maintenance = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernière maintenance")
    )
    next_maintenance = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Prochaine maintenance")
    )
    firmware_version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Version du firmware")
    )
    is_online = models.BooleanField(
        default=True,
        verbose_name=_("En ligne")
    )
    last_online = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Dernière connexion")
    )
    configuration = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Configuration")
    )

    class Meta:
        verbose_name = _("Lecteur NFC")
        verbose_name_plural = _("Lecteurs NFC")
        ordering = ['location', 'name']

    def __str__(self):
        return f"{self.name} ({self.location})"

# Modèle AccessPoint
class AccessPoint(TimeStampedModel):
    """Modèle pour gérer les points d'accès"""

    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    reader = models.OneToOneField(
        NFCReader,
        on_delete=models.CASCADE,
        related_name='access_point',
        verbose_name=_("Lecteur NFC")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    required_access_level = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Niveau d'accès requis")
    )
    allowed_departments = models.ManyToManyField(
        Department,
        blank=True,
        related_name='accessible_points',
        verbose_name=_("Départements autorisés")
    )
    schedule = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Horaires d'accès")
    )
    special_rules = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Règles spéciales")
    )

    class Meta:
        verbose_name = _("Point d'accès")
        verbose_name_plural = _("Points d'accès")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.reader.name}"

# Modèle AccessRule
class AccessRule(TimeStampedModel):
    """Modèle pour gérer les règles d'accès"""

    class RuleType(models.TextChoices):
        TIME_BASED = 'TIME_BASED', _('Basé sur le temps')
        ZONE_BASED = 'ZONE_BASED', _('Basé sur la zone')
        USER_BASED = 'USER_BASED', _('Basé sur l\'utilisateur')
        TEMPORARY = 'TEMPORARY', _('Temporaire')
        SPECIAL = 'SPECIAL', _('Spécial')

    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom de la règle")
    )
    rule_type = models.CharField(
        max_length=20,
        choices=RuleType.choices,
        default=RuleType.TIME_BASED,
        verbose_name=_("Type de règle")
    )
    access_point = models.ForeignKey(
        AccessPoint,
        on_delete=models.CASCADE,
        related_name='access_rules',
        verbose_name=_("Point d'accès")
    )
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name=_("Priorité")
    )
    conditions = models.JSONField(
        default=dict,
        verbose_name=_("Conditions")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de début")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de fin")
    )
    departments = models.ManyToManyField(
        Department,
        blank=True,
        related_name='access_rules',
        verbose_name=_("Départements")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )

    class Meta:
        verbose_name = _("Règle d'accès")
        verbose_name_plural = _("Règles d'accès")
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError(
                    _("La date de début doit être antérieure à la date de fin")
                )

class LoginAttempt(TimeStampedModel):
    """Trace les tentatives de connexion des utilisateurs pour prévenir les attaques par force brute."""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='login_attempts',
        verbose_name=_("Utilisateur")
    )
    ip_address = models.GenericIPAddressField(verbose_name=_("Adresse IP"))
    success = models.BooleanField(default=False, verbose_name=_("Succès"))
    user_agent = models.CharField(max_length=255, verbose_name=_("Agent utilisateur"))

    class Meta:
        verbose_name = _("Tentative de connexion")
        verbose_name_plural = _("Tentatives de connexion")
        ordering = ['-created_at']  # Utilisez 'created_at' ici

    def __str__(self):
        status = "Succès" if self.success else "Échec"
        user_str = self.user.username if self.user else "Utilisateur inconnu"
        return f"{user_str} - {status} - {self.ip_address} à {self.created_at}"
    
class UserSession(TimeStampedModel):
    """Suit et gère les sessions actives des utilisateurs."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_("Utilisateur")
    )
    session_key = models.CharField(max_length=40, unique=True, verbose_name=_("Clé de session"))
    ip_address = models.GenericIPAddressField(verbose_name=_("Adresse IP"))
    user_agent = models.CharField(max_length=255, verbose_name=_("Agent utilisateur"))
    last_activity = models.DateTimeField(default=timezone.now, verbose_name=_("Dernière activité"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    class Meta:
        verbose_name = _("Session utilisateur")
        verbose_name_plural = _("Sessions utilisateurs")
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} - {self.session_key} - {self.ip_address} - Active: {self.is_active}"
    
class PasswordReset(TimeStampedModel):
    """Gère les demandes de réinitialisation de mots de passe avec des tokens sécurisés."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_resets',
        verbose_name=_("Utilisateur")
    )
    token = models.CharField(max_length=255, unique=True, verbose_name=_("Token"))
    used = models.BooleanField(default=False, verbose_name=_("Utilisé"))
    ip_address = models.GenericIPAddressField(verbose_name=_("Adresse IP"))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("Créé le"))

    class Meta:
        verbose_name = _("Réinitialisation de mot de passe")
        verbose_name_plural = _("Réinitialisations de mot de passe")
        ordering = ['-created_at']

    def __str__(self):
        status = "Utilisé" if self.used else "Non utilisé"
        return f"{self.user.username} - {self.token} - {status} - {self.created_at}"