# Pubblicazione: GitHub → Medium

Il testo da pubblicare è [article.md](article.md), in inglese, con le cinque illustrazioni già collocate nel corpo dell’articolo. La versione HTML equivalente è [index.html](index.html). Il titolo, il sottotitolo, le sezioni, la citazione finale e i riferimenti esterni sono già formattati.

Il pacchetto è una conversione dell’ultima edizione LaTeX illustrata, datata 11 settembre 2026. Non occorre ricompilare il LaTeX o generare nuove immagini.

## Contenuto

```text
article.md                     Articolo completo in Markdown
index.html                     Pagina HTML pronta per GitHub Pages
images/
  01-blackboard.png
  02-artifactory-two-roles.png
  03-incident-timeline.png
  04-artifact-feedback-loop.png
  05-governed-blackboard.png
captions.md                    Didascalie e testi alternativi separati
build_preview.py               Rigenerazione HTML dopo modifiche al Markdown
.nojekyll                      File per la pubblicazione statica
README.md                      Questa guida; non fa parte dell’articolo
```

Le immagini sono i PNG originali approvati, ciascuno da 1448 × 1086 pixel. Non sono state ridisegnate, ritagliate o ingrandite. Le fonti dell’articolo sono collegamenti esterni effettivi; le immagini usano percorsi relativi, per esempio `images/01-blackboard.png`, senza nomi utente o repository da sostituire. GitHub supporta questo schema e raccomanda percorsi relativi per immagini nello stesso repository. [Documentazione GitHub](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#relative-links).

## Percorso diretto: Markdown su GitHub, poi copia e incolla

**1. Carica i file estratti, non lo ZIP.** In un repository dedicato, metti il contenuto di questa cartella nella radice. Mantieni `article.md` e la cartella `images/` allo stesso livello. Nell’interfaccia web di GitHub puoi usare **Add file → Upload files**, quindi confermare le modifiche con un commit. Se usi un repository esistente, puoi anche mettere l’intera cartella in una sottocartella: i riferimenti relativi resteranno coerenti. [Caricare file su GitHub](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository).

**2. Apri la versione formattata di `article.md`.** Controlla di vedere il titolo e tutte e cinque le immagini. Seleziona il contenuto visibile dell’articolo, non la visualizzazione **Raw** e non il codice dell’editor. Non copiare questa guida o l’interfaccia del repository.

**3. Incolla in una nuova bozza Medium.** Lavora preferibilmente da browser desktop. Per separare bene i campi, inserisci il titolo nel campo del titolo, il sottotitolo sotto di esso e copia il corpo a partire da “One agent does not need a chat tool…”. La firma e la data sono disponibili all’inizio del Markdown; puoi mantenerle nel corpo oppure affidare la firma al profilo Medium. La migrazione manuale tramite copia e incolla, seguita dall’aggiunta degli elementi mancanti, è il percorso descritto da Medium. [Guida Medium alla migrazione manuale](https://help.medium.com/hc/en-us/articles/360033931713-Trouble-importing-content-using-the-import-tool).

**Controlla sempre le immagini nella bozza.** Non è garantito che il browser e l’editor trasferiscano tutte le immagini e le didascalie insieme al testo. Se una figura manca, carica il PNG corrispondente da `images/`, nella posizione indicata dal Markdown. Caricare i file singolarmente evita di dover riordinare una griglia. Il file `captions.md` contiene il testo di ogni didascalia e il relativo *alt text*. Medium consente upload PNG, didascalie e testo alternativo; le immagini incluse sono entro il limite documentato di 25 MB per file e superano i 1192 pixel di larghezza necessari per tutte le opzioni di posizionamento. [Guida Medium alle immagini](https://help.medium.com/hc/en-us/articles/215679797-Using-images).

## Pagina pulita da copiare: GitHub Pages

Per evitare di selezionare anche elementi dell’interfaccia di GitHub, puoi pubblicare `index.html` come pagina web autonoma. È già pronta: non occorrono framework, dipendenze web o un nuovo rendering del Markdown.

Con i file nella radice del repository, apri **Settings → Pages**. In **Build and deployment**, scegli **Deploy from a branch**, seleziona il branch che contiene i file, ad esempio `main`, e la cartella **/(root)**; poi salva. Usa l’indirizzo del sito mostrato da GitHub dopo la pubblicazione. Un repository pubblico è la soluzione più semplice per rendere articolo e figure accessibili senza autenticazione. [Configurazione GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Apri quella pagina e copia il contenuto formattato in Medium. Il normale collegamento GitHub al file `index.html` mostra il sorgente: per leggere la pagina pubblicata devi usare l’indirizzo di **GitHub Pages**.

In alternativa al copia e incolla, prova **Stories → Import a story** su Medium con l’indirizzo pubblico della pagina HTML. Non usare il codice Raw o l’indirizzo di visualizzazione del file nel repository come sorgente di importazione consigliata. Medium documenta l’importazione da un URL e l’aggiunta automatica di un collegamento *canonical* alla fonte, ma l’estrazione può fallire: resta necessario verificare la bozza e, se serve, procedere manualmente. [Importazione su Medium](https://help.medium.com/hc/en-us/articles/214550207-Importing-a-post-to-Medium).

Il collegamento canonical indica quale pagina è considerata l’originale. Con il copia e incolla non presumere che sia già impostato: Medium permette di aggiungerlo manualmente. Per questa scelta usa l’URL della pagina dell’articolo che vuoi considerare originale, non la pagina generica del repository. [Migrazione manuale e canonical](https://help.medium.com/hc/en-us/articles/360033931713-Trouble-importing-content-using-the-import-tool).

## Controllo finale nella bozza Medium

Verifica titolo e sottotitolo, gerarchia delle sezioni, ordine delle cinque figure e leggibilità delle scritte. Controlla che didascalie e testi alternativi non siano scomparsi, che i link alle fonti siano cliccabili e che la citazione finale conservi la formattazione. Mantieni le distinzioni esplicite fra ricostruzione dell’incidente, illustrazioni concettuali e architettura proposta.

Per l’immagine di anteprima puoi scegliere la Figura 1, già inclusa nell’articolo. L’impostazione dell’immagine di anteprima è disponibile nella procedura di pubblicazione di Medium. [Impostazioni di pubblicazione](https://help.medium.com/hc/en-us/articles/360033931713-Trouble-importing-content-using-the-import-tool).

## Modifiche successive

`article.md` è il master editoriale. Per pubblicare i file già pronti non serve installare nulla. Soltanto dopo aver modificato il Markdown, rigenera `index.html` con Python 3.9 o successivo e [Pandoc](https://pandoc.org/installing.html) installati:

```bash
python build_preview.py
```

Per generare una pagina HTML autonoma da leggere offline, con le immagini incorporate:

```bash
python build_preview.py --embed-images --output preview.html
```

La pagina autonoma serve come anteprima locale. Per il passaggio a Medium usa preferibilmente la pagina pubblica con le normali immagini PNG, oppure carica le figure direttamente nella bozza. L’HTML viene generato dal Markdown, non è un secondo master da mantenere separatamente.
