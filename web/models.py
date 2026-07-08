from django.db import models
from django.conf import settings
from django.db.models import Q


class Zug(models.Model):
    STATUS_CHOICES = [
        ('WARTET', 'Wartet am Einfahrtssignal'),
        ('FAHRT', 'Fährt in den Bahnhof ein'),
        ('GEPARKT', 'Steht am Gleis'),
        ('ABGEFAHREN', 'Hat den Bahnhof verlassen'),
    ]

    zug_nummer = models.CharField(max_length=20, unique=True, verbose_name="Zug-ID (z.B. ICE 721)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WARTET')
    aktualisiert_am = models.DateTimeField(auto_now=True)
    lokfuehrer = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Fahrt',
        related_name="zuege",
        blank=True,
        verbose_name="Lokführer"
    )

    class Meta:
        verbose_name = "Zug"
        verbose_name_plural = "Züge"

    def __str__(self):
        return f"{self.zug_nummer} ({self.get_status_display()})"


class Fahrt(models.Model):
    zug = models.ForeignKey(Zug, on_delete=models.CASCADE)
    lokfuehrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fahrt_beginn = models.DateTimeField(null=True, blank=True, verbose_name="Fahrtbeginn")
    fahrt_ende = models.DateTimeField(null=True, blank=True, verbose_name="Fahrtende")

    class Meta:
        verbose_name = "Fahrt"
        verbose_name_plural = "Fahrten"

        # Hier kommen die Sicherheitsregeln rein:
        constraints = [
            # Regel 1: Ein Lokführer darf maximal EINE aktive Fahrt (fahrt_ende ist leer) haben
            models.UniqueConstraint(
                fields=['lokfuehrer'],
                condition=Q(fahrt_ende__isnull=True),
                name='ein_lokfuehrer_pro_aktive_fahrt'
            ),
            # Regel 2: Ein Zug darf maximal EINE aktive Fahrt haben
            models.UniqueConstraint(
                fields=['zug'],
                condition=Q(fahrt_ende__isnull=True),
                name='ein_zug_pro_aktive_fahrt'
            )
        ]

    def __str__(self):
        return f"{self.lokfuehrer} fährt {self.zug}"

class Gleis(models.Model):
    gleis_nummer = models.CharField(max_length=10, unique=True, verbose_name="Gleisnummer")
    # Der Sensor liefert True (belegt) oder False (frei)
    sensor_belegt = models.BooleanField(default=False, verbose_name="Sensor: Gleis belegt?")
    laenge_meter = models.PositiveIntegerField(default=300, verbose_name="Gleislänge in Metern")

    class Meta:
        verbose_name = "Gleis"
        verbose_name_plural = "Gleise"

    def __str__(self):
        zustand = "🔴 BELEGT" if self.sensor_belegt else "🟢 FREI"
        return f"Gleis {self.gleis_nummer} - {zustand}"


class Fahrstrasse(models.Model):
    """
    Sorgt für die Kollisionserkennung.
    Ein Gleis darf aktiv immer nur für maximal einen Zug reserviert sein!
    """
    zug = models.ForeignKey(Zug, on_delete=models.CASCADE, related_name="reservierungen")
    gleis = models.ForeignKey(Gleis, on_delete=models.CASCADE, related_name="reservierungen")
    # Eine Reservierung ist aktiv, solange der Zug die Fahrstraße nutzt
    ist_aktiv = models.BooleanField(default=True, verbose_name="Fahrstraße freigeschaltet (Reserviert)")
    freigeschaltet_um = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Einzigartigkeits-Constraint: Ein Gleis darf nicht doppelt aktiv reserviert werden!
        # Das fängt Kollisionen bereits auf Datenbank-Ebene ab.
        verbose_name = "Fahrstraße"
        verbose_name_plural = "Fahstraßen"
        constraints = [
            models.UniqueConstraint(
                fields=['gleis'],
                condition=models.Q(ist_aktiv=True),
                name='einzigartige_aktive_gleis_reservierung'
            )
        ]


    def __str__(self):
        status = "Aktiv" if self.ist_aktiv else "Beendet"
        return f"Fahrstraße: {self.zug.zug_nummer} ➡️ Gleis {self.gleis.gleis_nummer} ({status})"


class StellwerkAnfrage(models.Model):
    """ Das Kommunikationsprotokoll zwischen Lok und Stellwerk """
    ERGEBNIS_CHOICES = [
        ('OFFEN', 'In Bearbeitung / Zug wartet'),
        ('GENEHMIGT', 'Einfahrt erlaubt'),
        ('ABGEWIESEN', 'Kein Gleis frei / Bitte warten'),
        ('BEENDEN', 'Abgeschlossen'),
    ]

    zug = models.ForeignKey(Zug, on_delete=models.CASCADE)
    anfrage_zeit = models.DateTimeField(auto_now_add=True)
    ergebnis = models.CharField(max_length=20, choices=ERGEBNIS_CHOICES, default='OFFEN')
    zugewiesenes_gleis = models.ForeignKey(Gleis, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Stellwerkanfrage"
        verbose_name_plural = "Stellwerkanfragen"

    def __str__(self):
        return f"Anfrage von {self.zug.zug_nummer} um {self.anfrage_zeit.strftime('%H:%M:%S')}: {self.get_ergebnis_display()}"