14. Oktober 2013
================

Das erste Problem wurde gesichtet: Genre Normalisierung. (Ich nenn es Sören.)
Lösungsansatz mit einem Genre-Baum der von einer Genre-Liste von echonest
abgeleitet wurde. Funktioniert eigentlich ganz anständig. Was fehlt wäre noch
ein backtracking algorithmus der für folgendes genre alle möglichen resultate
liefert: ::

    >>> match('Pure Depressive Black Funeral Doom Metal')  # yap, wirklich.
    [('doom', 'funeral'), ('metal', 'black', 'pure'), ('metal', 'black', 'depressive')]

    # Anmerkung: Geschafft! unter build_genre_path_all() verfügbar.

- Die Resultate sind natürlich so gut wie Datenbank und wie der Input.
- Der Input ist besonders schwierig da sich weder Fans noch Labels noch die
  einzelnen Mitglieder einer Band unter Umständen auch nur auf das genre eines
  einzelnen Albums einigen können.

  Anektode dazu: Varg Vikernes, damals Gitarrist der Band Mayhem, ermordete den 
  damaligen Frontmann unter anderen wegen Meinungsverschiedenheit ob die Band
  denn nun reinen 'Black Metal' oder doch eher 'Depressive Black Metal' spiele.
- http://ikeaordeath.com/ ist eine passende Hommage für das Thema.
  Man beachte die teilweise angegebenen Genre Namen!
