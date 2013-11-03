Logbuch: developement log (german)
==================================

14. Oktober 2013
----------------

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

15. Oktober 2013
----------------

Die tolle iisys Hardware macht mal wieder Probleme. Heureka. Kein Internet.

- Es gibt eine ganze Forschungsrichtung für das was ich mach: MIR - Music
  Information Retrieval. Gibt sogar teils schon Frameworks dazu wie MARYSAS.
  Auf deren Seite gibts auch eine Datensets (nicht frei aber) mit getaggten
  Genres. Allerdings als .wav files:

    http://marsyas.info/

16. Oktober 2013
----------------

Hardware geht wieder... waren zu blöd zu merken dass es da noch ne externe NIC
gab. Die geht dann auch problemlos. Schade dass wir dafür nicht bezahlt wurden
wie unsere *Kollegen*. Hatte die Idee für Distanzen noch allgemein "Regeln"
einzuführen. Beispielsweise eine Distanzfunktion kann einen Wert berechnen, aber 
dieser kann von einer Regel überschrieben werden. 

Zurück zu unserem Genre Beispiel:

    Die beiden Pfade (190, 0) und (175, 1) sollen 'folk metal' und 'folk rock'
    sein. Beide haben aber wie man sieht komplett unterschiedliche Pfade und
    bekämen daher eine Distanz von 1.0 zugewisen - obwohl beide genres jetzt
    nicht sehr weit entfernt sind. Daher könnten Regeln eingeführt werden die
    für bestimmte Pfade, oder allgemein Werte eine bestimmte Distanz festlegt. 
    Diese Regeln könnten dann beispielsweise dynamisch durch Apriori oder auch
    manuell durch den User eingepflegt werden.

Ein Problem dass gelöst werden will:

    Was passiert wenn man zu einem bestimmten Song nur Songs suchen will die in
    bestimmten Attributen ähnlich sind, beispielsweise ähnliches genre?

    Einfach weiter im Graph traversieren und nur Attribute mit dieser lokalen 
    Attributmaske betrachten?


17. Oktober 2013
----------------

Problem: (Ich nenns mal Sam): https://gist.github.com/sahib/7013716

Lösung war jetzt am Ende einfach: Man nehme die Single Linkage beider Cluster.
Mit anderen Worten: Die kleinste Distanz die beim Vergleichen aller Elemente mit
allen Elementen der anderen Liste entsteht. Ist einfach zu erklären  und gibt im
Grunde die ordentlichsten und realitätsnahesten Ergebnisse beim Vergleichen von
Genres.


- class Distance: Diese Klasse könnte bereits Regeln einführen und allgemein
  implementieren. 

  Eine REgel wäre zB: 'rock' ==> 'metal':0.0 (wieder bei unseren genre beispiel,
  soll aber allgemein sein). Die Regel heißt: Wer rock hört, hört mit einer
  hohen Wahrscheinlichkeit auch metal. Die 0.0 ist die Distanz die dafür
  angenommen wird (maximale ähnlichkeit.). Regeln können auch bidirektional sein:

    'rock' <=> 'metal':0.0

  in diesem Fall gilt auch das Inverse: Wer gern Metal hört, hört auch gern Rock.


23. Oktober 2013
----------------

Das Grobe Design steht im Grunde. Es wurde ein sphinx-dummy erstellt der auf RTD 
auch buildet. Unittest wurden für die meisten Module bereits implementiert,
und bei jedem commit laufen die für python3 und python2 durch. Praktisch :)

Grober Plan ist bis ca. 10.11 einen groben Prototypen fertig zu haben. 

Sonstige Neuerungen:

- Ein AtticProvider wurde implementiert. (Caching von input values)
- Eine Songklasse wurde implementiert (ein readonly Mapping) 
  Diese sollen dann später auch die Distanzen zu allen anderen Songs kennen.

28. Oktober 2013
----------------

Gestern noch einen bugreport bei Readthedocs gefiled, die pushen auch gleich auf
den produktionserver ohne vorher zu testen. überall Helden :)
Hoffentlich geht der buidl bald wieder.

Heute das erste mal in der Doku das Wort "injektiv" (oder auch umkehrbar
gnnant) benutzt. Fühl mich wie in Mathematikerelch. Bin mit dem Fahrrad in die
FH gefahren, Zwille hat in Mathe wieder Matrizen bei Koeffizienten gesehen...
Also ganz normal der Tag bisher.

30. Oktober 2013
----------------

Heute lange Diskussion mit Katzen über beide Projekte (morgen nochmal
detailliert über seins). Neue Erkenntnis:

    - Regeln gelten pro Key in der Attributmaske
    - Eine Distanzmatrix ist schlicht zu teuer.
    - Graph wird direkt aus Songliste gebaut. 
    - Jeder Song speichert N ähnlichste Songs. (N wählbar, sessionweit)

Sonstiger Grundtenor: Die Lösung ist schenjal. Im Babsi-Sinne, also negativ :)

Damit ich jetzt nochmal das Theme dastehen habe:

  | Implementierung und Evaluierung eines Musikempfehlungssytems basierend auf Datamining Algorithmen


4. November 2013
----------------

Einiges ist nun etwas gefestigt. Session caching ist implementiert. 

Eine interessanter Vergleich von Graph-Performance:

    http://graph-tool.skewed.de/performance

Stimmt wohl gar nicht dass NetworkX meist fast gleich schnell ist. Hätte mich
auch gewundert. Der Benchmarkgraph hat dann sogar vermutlich die gleich
Dimensionen wie bei mir. 15 Stunden für "betweenness" ist daher kaum
vertretbar. 

**Nächste Schritte:**

    * Graph builden (auf library einigen)
    * Sich auf Datamining Framework einigen. (TextBlob? aber kein stemmer)
    * ``__main__.py`` schreiben.
    * moosecat auspacken, an mpd 0.18 anpassen und daten mal in libmunin
      reinschauffeln.
