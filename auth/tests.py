from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group


class UserAuthenticationIntegrationTest(TestCase):

    def setUp(self):
        """
        Setzt die benötigte Testumgebung vor jedem Testlauf auf.
        """
        # Da das Formular eine Rolle (Gruppe) erfordert, erstellen wir eine Testgruppe
        self.test_group = Group.objects.create(name="Fahrdienstleiter")

        # URLs aus dem URLconf auflösen (Namen müssen mit urls.py übereinstimmen)
        self.register_url = reverse('register')
        self.login_url = reverse('login')

    def test_registration_and_login_flow(self):
        """
        Szenario: Ein neuer Benutzer lädt die Registrierungsseite, füllt das Formular aus,
        wird in der Datenbank angelegt und kann sich anschließend erfolgreich einloggen.
        """

        # 1. Test: Laden der Registrierungsseite prüfen (Status 200)
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200, "Die Registrierungsseite konnte nicht geladen werden.")

        # 2. Test: Ausfüllen des Formulars und Erstellung des Benutzers simulieren
        registration_data = {
            'username': 'testzugfuehrer',
            'email': 'zug@projekt.de',
            'password1': 'SicheresPasswort123!',
            'password2': 'SicheresPasswort123!',
            'role': self.test_group.id
        }

        # Formular absenden (POST)
        post_response = self.client.post(self.register_url, data=registration_data)

        # Nach erfolgreicher Registrierung leitet Django meistens weiter (Status 302)
        self.assertEqual(post_response.status_code, 302, "Die Formularübermittlung war nicht erfolgreich.")

        # 3. Test: Überprüfung, ob der Benutzer korrekt in der Datenbank existiert
        user_exists = User.objects.filter(username='testzugfuehrer').exists()
        self.assertTrue(user_exists, "Der Benutzer wurde nicht in der Datenbank angelegt.")

        # Prüfen, ob die zugewiesene Rolle (Gruppe) stimmt
        new_user = User.objects.get(username='testzugfuehrer')
        self.assertTrue(new_user.groups.filter(id=self.test_group.id).exists(),
                        "Die Rolle wurde dem Benutzer nicht zugewiesen.")

        # 4. Test: Laden der Login-Seite prüfen (Status 200)
        login_page_response = self.client.get(self.login_url)
        self.assertEqual(login_page_response.status_code, 200, "Die Login-Seite konnte nicht geladen werden.")

        # 5. Test: Einloggen mit den neuen Zugangsdaten prüfen
        login_success = self.client.login(username='testzugfuehrer', password='SicheresPasswort123!')
        self.assertTrue(login_success, "Der Login-Vorgang mit den neuen Benutzerdaten ist fehlgeschlagen.")





