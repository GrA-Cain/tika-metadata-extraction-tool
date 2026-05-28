## Table of Contents

- [Tika-metadata-tool](#Tika-metadata-tool)
	- [Achtergrond informatie](#Achtergrond-informatie)
	- [Installatie](#installatie)
	- [Gebruik](#Gebruik)
   - [Feature suggesties en bugs](#Feature-suggesties-en-bugs)
	- [Contributors](#Contributors)
	- [Licensie](#Licensie)

## Achtergrond informatie
De Metadata Tool is een Python-gebaseerde applicatie voor het extraheren, visualiseren en exporteren van metadata uit digitale bestanden. De tool is ontwikkeld voor archieven die in tijden van digitalisering steeds meer te maken krijgen met het metadatateren van bestanden. Met behulp van Apache Tika worden metadata automatisch uit bestanden geëxtraheerd en opgeslagen als sidecar-bestanden. De geëxtraheerde metadata kan vervolgens worden gevisualiseerd en geanalyseerd via een interactieve gebruikersinterface, en geëxporteerd naar Excel voor verdere verwerking. De tool is zo veel mogelijk met flexibiliteit in gedachten ontworpen, het idee is dat gebruikers kunnen zelf bepalen welke metadata velden worden meegenomen, hoe de output wordt gestructureerd, en welke bestandstypen worden verwerkt.

## Installatie
Voor het gebruik van de Metadata Tool is het volgende vereist:

* Python 3.10 of hoger: te downloaden via python.org

* Java 8 of hoger:  (vereist voor Apache Tika)  te downloaden via java.com

* Apache Tika: voor het extraheren van metadata. Raadpleeg de officiële Tika documentatie voor installatie-instructies. Plaats het tika.jar bestand in de hoofdmap van het project (is standaard als je de libary cloned, voor de meest recente versie van het bestand: https://tika.apache.org/download.html)


**Python packages**

Installeer de benodigde Python packages via pip:
```bash
pip install -r requirements.txt
```

## Gebruik
De applicatie wordt gestart via de terminal:
```bash
streamlit run app.py
```
De interface bestaat uit vier tabbladen:
1. Genereren metadata (Tika)
In dit tabblad wordt Apache Tika gebruikt om metadata uit bestanden te extraheren. De gebruiker specificeert een root directory en de tool leest de metadata recursief uit. De geëxtraheerde metadata wordt standaard opgeslagen als sidecar-bestand naast het originele bestand. Optioneel kan een alternatieve outputmap worden opgegeven.

2. Metadata visualisatie
Dit tabblad biedt een interactieve omgeving voor het analyseren en exporteren van de geëxtraheerde metadata in Excel formaat. De gebruiker kan:

* Specifieke DataFrames selecteren en exporteren naar Excel

* Een voorbeeld van een DataFrame bekijken in de interface

* Beschrijvende statistieken toevoegen aan de output

* Een steekproef nemen van de data
  
* Duplicaten tussen kolommen analyseren

3. Metadata selectie
In dit tabblad worden de geëxtraheerde metadata velden gefilterd en opgeslagen als .metadata.json of .metadata.yaml sidecar-bestanden. De selectie is gebaseerd op vooraf gedefinieerde metadata structuren per bestandstype. (Zie class variables MetaDataPipeline in src/metadata_pipine.py)

4. Metadata files verwijderen
Dit tabblad biedt functionaliteit voor het verwijderen van gegenereerde metadata bestanden. Standaard worden alleen .metadata.json bestanden verwijderd. Optioneel kunnen ook alle .json bestanden of .yaml bestanden worden verwijderd.
tuturial format

## Feature suggesties en bugs
* FEATURE: Om .metadata.json files te genereren moet je de code in duiken (metadatapipeline class variable dictionary's) om de output te veranderen, dit moet flexibel in de UI kunnen
* FEATURE: "Group" DataFrames zijn hardcoded in de DataFramePipeline, alhoewel het relatief makkelijk is om nieuwe groups toe te voegen moet je hier ook de code in duiken. Daarbij worden "groups" en "namespace" als synoniem gebruikt, dit moet uniform. Er moet dus een feature ontwikkeld worden zodat je makkelijk nieuwe groups kan toevoegen en groups kan verwijderen.
* BUG?: Alleen getest op een testset van ~200 files (.docx, .pdf, .msg, .jpg en .xlsx). Sommige functionaliteit (zoals duplicaten analyse) moet wellicht geoptimaliseerd worden als je met grote datasets werkt.
* BUG: het specificeren van een output_dir in het genereren van metadata output alle bestanden in de juiste directory structuur maar output ook alles in de root directory. Raadpleeg metadata_pipeline.py (method: metadata_genereren()) voor fix.
* FEATURE: Sample fractie voor het previewen van DataFrames
* FEATURE: Het customizen van Apachi Tika parameters in de CLI call tijdens het genereren van metadata


### Autheurs
[@Marco Venema](https://github.com/marcovenema). #Author

## Licensie
Add license info
