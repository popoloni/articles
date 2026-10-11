# Qwen e Bonsai sul Mac mini M4 con 16 GB
## Installazione, esecuzione e prove standalone — prima di Kowalski

Verifica documentale: 5 ottobre 2026.

Questa guida non modifica Kowalski, non installa un orchestratore e non avvia agenti con accesso a file o shell. Prima si verifica che ciascun modello funzioni da solo, con il proprio runtime e una piccola API locale.

**Limite di validazione:** i comandi di inferenza sono ricette ricavate dalle fonti primarie citate, non prove effettuate da noi su un Mac M4. Il client `smoke_test.py` è stato invece eseguito e verificato su Linux con un server HTTP fittizio: 14 test passati. Il suo successo non dimostra che i modelli o Metal funzionino sul Mac. Nessun peso è incluso nel pacchetto.

## 1. Quali tre modelli, e quali evidenze

| Modello esatto | Runtime scelto | Dimensione dei pesi/artifact, non memoria totale |
|---|---|---|
| `manjunathshiva/Qwen3.6-35B-A3B-tq3a-tqTe-down4-g64` | TurboQuant-MLX, `turboquant-serve` | circa 12,6 GB = 11,7 GiB |
| `inductiveML/Ternary-Bonsai-27B-mlx-lossless-1.75bpw` | MLX-LM e codice Metal incluso nel checkpoint | 5.888.388.744 byte, circa 5,89 GB = 5,48 GiB |
| `prism-ml/Bonsai-27B-gguf`, file `Bonsai-27B-Q1_0.gguf` | llama.cpp / Metal | circa 3,8 GB |

GB indica 10^9 byte; GiB indica 2^30 byte. Dimensione del file, memoria del modello e memoria dell'intero sistema sono misure diverse. [S1–S3]

Il manutentore TurboQuant riporta una prova sul **Mac mini base M-series da 16 GB**: 15,2–15,6 token/s e tre completamenti della stessa piccola attività agentica. Quella sezione non identifica inequivocabilmente il chip come M4. È evidenza utile, non un benchmark indipendente di affidabilità generale. [S1]

Il repack ternario documenta misure su **M4 Max con 48 GB**, pur dichiarando 16 GB come requisito minimo: non trasferire la velocità del Max al Mini. Per il binary esiste anche una prova comunitaria su **M3 Air 16 GB con MLX**, quindi su hardware/runtime diversi dal percorso GGUF qui proposto. [S2, S4]

**Ordine che suggerisco:** binary → ternary → TurboQuant. Si comincia dalla configurazione con più margine, si verifica il metodo, e solo dopo si prova quella più stretta. È una scelta operativa della guida, non una classifica di qualità dimostrata.

## 2. Preparazione comune

Salva il lavoro; per le prime prove chiudi altri server LLM, VM, Docker e applicazioni pesanti. Tieni aperto Monitoraggio Attività → Memoria. Usa un solo modello alla volta: disporre di tre porte non significa avere memoria per tre server.

Apri un Terminale nativo, non tramite Rosetta:

```bash
uname -m
sysctl -n hw.memsize
sw_vers
xcode-select -p
```

`uname -m` deve essere `arm64`. La compatibilità macOS va verificata rispetto alla versione MLX installata; non forzare wheel incompatibili o Python x86_64. [S5]

Se mancano i Command Line Tools, esegui `xcode-select --install` e completa l'installazione prima di continuare. I comandi successivi presuppongono Homebrew già installato secondo la sua documentazione ufficiale. [S6]

```bash
brew install python@3.11 git

export LAB="$HOME/qwen-m4-16gb"
mkdir -p "$LAB/models" "$LAB/logs"

cat > "$LAB/lab.env" <<'EOF'
export LAB="$HOME/qwen-m4-16gb"
set -o pipefail
EOF

PY="$(brew --prefix python@3.11)/bin/python3.11"
"$PY" -m venv "$LAB/venv-tools"
"$LAB/venv-tools/bin/python" -m pip install --upgrade pip huggingface_hub
"$LAB/venv-tools/bin/python" -m pip freeze > "$LAB/logs/tools.freeze.txt"

df -h "$LAB"
sysctl vm.swapusage
```

Suggerisco circa 40 GB liberi per questo laboratorio, inclusi runtime, log e margine operativo; non è un requisito ufficiale dei modelli. Evita di duplicare i download tra directory locali e cache di applicazioni differenti. `hf download --local-dir` mantiene i file nella directory scelta. [S7]

### Scaricare una revisione precisa

Per non confondere in futuro un nuovo checkpoint con quello provato oggi, usa questa funzione nel terminale dei download:

```bash
source "$HOME/qwen-m4-16gb/lab.env"

fetch_model() {
  local repo="$1"
  local dest="$2"
  shift 2
  local rev
  rev="$("$LAB/venv-tools/bin/python" -c \
    'from huggingface_hub import HfApi; import sys; print(HfApi().model_info(sys.argv[1]).sha)' \
    "$repo")" || return 1
  mkdir -p "$dest" || return 1
  "$LAB/venv-tools/bin/hf" download "$repo" "$@" \
    --revision "$rev" --local-dir "$dest" || return 1
  printf '%s\n%s\n' "$repo" "$rev" > "$dest/DOWNLOADED_REVISION.txt"
}
```

La funzione legge lo SHA corrente e scarica proprio quello. Il relativo `DOWNLOADED_REVISION.txt` identifica i file di quel test; non equivale a una revisione di sicurezza. Non sostituire manualmente i file con versioni di altre revisioni. [S7]

## 3. Bonsai binary: il percorso iniziale più semplice

### 3.1 Scarica solo il GGUF richiesto

Nel terminale in cui hai definito `fetch_model`:

```bash
fetch_model prism-ml/Bonsai-27B-gguf \
  "$LAB/models/bonsai-binary" Bonsai-27B-Q1_0.gguf LICENSE.txt NOTICE.txt
```

Non scaricare indiscriminatamente l'intero repository: comprende anche il file F16 da circa 53,8 GB e artefatti aggiuntivi. Qui non servono modello draft, proiettore visivo o interfaccia web esterna. [S3]

### 3.2 Installa i binari distribuiti dal progetto PrismML

Q1_0 è supportato da llama.cpp/Metal; il binary MLX richiede invece il fork MLX indicato da Prism. Scelgo GGUF per evitare quella compilazione nel primo giro. Inoltre il progetto demo oggi seleziona **Bonsai 2** per default: il percorso qui usa un file esplicito di **Bonsai 1** e non delega la scelta al default. [S8]

```bash
git clone --depth 1 https://github.com/PrismML-Eng/Bonsai-demo.git \
  "$LAB/Bonsai-demo"

git -C "$LAB/Bonsai-demo" rev-parse HEAD > "$LAB/logs/bonsai-demo.commit.txt"

# Esamina gli script prima di eseguirli.
less "$LAB/Bonsai-demo/scripts/download_binaries.sh"
less "$LAB/Bonsai-demo/scripts/common.sh"

bash "$LAB/Bonsai-demo/scripts/download_binaries.sh"
"$LAB/Bonsai-demo/bin/mac/llama-cli" --version
cat "$LAB/Bonsai-demo/bin/mac/.llama_release"
```

Lo script consultato scarica la release `prism-b10743-adfffbe`, rileva l'architettura e colloca i binari in `bin/mac`. Rimuove gli attributi di quarantena nella directory scaricata e applica una firma ad hoc: questo comportamento va accettato consapevolmente, non confuso con una certificazione Apple. Non disabilitare Gatekeeper globalmente. Non eseguiamo `setup.sh`, che prepara uno stack più ampio. [S9]

### 3.3 Una prima generazione breve

```bash
source "$HOME/qwen-m4-16gb/lab.env"

"$LAB/Bonsai-demo/bin/mac/llama-cli" \
  -m "$LAB/models/bonsai-binary/Bonsai-27B-Q1_0.gguf" \
  -ngl 99 -fa on -c 4096 -n 512 \
  --temp 0.7 --top-p 0.95 --top-k 20 --min-p 0 \
  --reasoning-budget 0 \
  --chat-template-kwargs '{"enable_thinking":false}' \
  -st -p 'Spiega in italiano la differenza tra retry e rollback, in cinque frasi.' \
  2>&1 | tee "$LAB/logs/binary-generate.log"
```

Questa è una configurazione iniziale non-thinking, non la riproduzione dei benchmark di ragionamento pubblicati. `-c 4096` definisce il contesto del processo; `-n 512` limita questa generazione; `-st` termina dopo il turno. Controlla nei log che Metal sia effettivamente utilizzato. La sintassi è coerente con il launcher del progetto. [S10]

### 3.4 Avvia il server locale

Dopo la fine della generazione, nello stesso terminale:

```bash
"$LAB/Bonsai-demo/bin/mac/llama-server" \
  -m "$LAB/models/bonsai-binary/Bonsai-27B-Q1_0.gguf" \
  --host 127.0.0.1 --port 8082 --alias bonsai-binary \
  -ngl 99 -fa on -c 4096 -np 1 \
  --jinja --temp 0.7 --top-p 0.95 --top-k 20 --min-p 0 \
  --reasoning-budget 0 \
  --chat-template-kwargs '{"enable_thinking":false}' \
  2>&1 | tee "$LAB/logs/binary-server.log"
```

Qui `--jinja` consente l'uso del chat template per le chiamate strutturate; il server resta sull'interfaccia locale. La richiesta API deve comunque specificare `max_tokens`. Nessun tool viene eseguito dal nostro test. [S11]

Dopo le prove della sezione 6, ferma il server con **Ctrl+C** e attendi che la memoria sia rilasciata.

## 4. Ternary Bonsai MLX: il checkpoint compatto 1,75 bpw

### 4.1 Crea un ambiente separato

Riprendo la coppia MLX/MLX-LM dichiarata nelle misure del repack, non una combinazione universale per qualunque release futura. [S2]

```bash
source "$HOME/qwen-m4-16gb/lab.env"
PY="$(brew --prefix python@3.11)/bin/python3.11"
"$PY" -m venv "$LAB/venv-ternary"

"$LAB/venv-ternary/bin/python" -m pip install --upgrade pip
"$LAB/venv-ternary/bin/python" -m pip install \
  "mlx==0.32.0" "mlx-lm==0.31.3" "transformers!=5.13.*"
"$LAB/venv-ternary/bin/python" -m pip check
"$LAB/venv-ternary/bin/python" -m pip freeze > "$LAB/logs/ternary.freeze.txt"
```

L'esclusione di Transformers 5.13.* è una precauzione di compatibilità presente nello stack TurboQuant, mantenuta qui per non introdurre quella versione nel laboratorio; non è una nuova garanzia di compatibilità end-to-end. [S14]

### 4.2 Scarica ed esamina il codice del checkpoint

Nel terminale dei download:

```bash
fetch_model inductiveML/Ternary-Bonsai-27B-mlx-lossless-1.75bpw \
  "$LAB/models/bonsai-ternary-175"

less "$LAB/models/bonsai-ternary-175/ternel_packed_model.py"
less "$LAB/models/bonsai-ternary-175/ternel_manifest.json"
shasum -a 256 "$LAB/models/bonsai-ternary-175/ternel_packed_model.py" \
  > "$LAB/logs/ternary-code.sha256.txt"
```

**Non è solo un insieme di pesi:** questo checkpoint usa codice Python e kernel Metal propri, richiamati da `config.json`. La versione 0.31.3 li può caricare senza una conferma esplicita; release successive possono richiedere `--trust-remote-code`. Leggere il codice e conservarne l'hash non ne certifica la sicurezza: procedi solo se consideri attendibile quella revisione. Ternel pubblica sorgenti e verifiche di fedeltà del repack. [S2, S12]

### 4.3 Prima generazione

```bash
"$LAB/venv-ternary/bin/mlx_lm.generate" \
  --model "$LAB/models/bonsai-ternary-175" \
  --prompt 'Spiega in italiano la differenza tra retry e rollback, in cinque frasi.' \
  --max-tokens 512 --temp 0.7 --top-p 0.95 --top-k 20 \
  --chat-template-config '{"enable_thinking":false}' \
  2>&1 | tee "$LAB/logs/ternary-generate.log"
```

In **generate 0.31.3** l'opzione è `--chat-template-config`. Non aggiungere `--prefill-step-size` a questo comando: quell'opzione non è esposta dalla CLI di generazione di questa versione. [S13]

### 4.4 Server con una sola richiesta concorrente

```bash
"$LAB/venv-ternary/bin/mlx_lm.server" \
  --model "$LAB/models/bonsai-ternary-175" \
  --host 127.0.0.1 --port 8081 \
  --temp 0.7 --top-p 0.95 --top-k 20 --max-tokens 1024 \
  --chat-template-args '{"enable_thinking":false}' \
  --prompt-concurrency 1 --decode-concurrency 1 \
  --prefill-step-size 128 --prompt-cache-size 1 \
  2>&1 | tee "$LAB/logs/ternary-server.log"
```

In **server 0.31.3** l'opzione è invece `--chat-template-args`. Questa versione non espone `--kv-bits` nel server, benché la CLI di generazione lo esponga. `--prompt-cache-size 1` limita le cache conservate, non impone una lunghezza massima al prompt; `--max-tokens` è un default, non una quota inderogabile. Per questo laboratorio usa richieste corte e un solo client. È un server di sviluppo, non un servizio da esporre in rete. [S15]

Il modello 1,75 bpw non è necessariamente il più veloce: il confronto del manutentore favorisce il formato ufficiale 2-bit in velocità. Come controllo opzionale puoi scaricare `prism-ml/Ternary-Bonsai-27B-mlx-2bit` e usare lo stesso ambiente con un percorso diverso, sempre un processo per volta. Richiede più memoria ma evita il loader custom del repack. [S2, S8]

## 5. Qwen MoE TurboQuant asimmetrico: prova con poco margine

### 5.1 Installa il suo runtime, senza contaminarlo con fork MLX

La distribuzione verificata su PyPI è `turboquant-mlx-full==0.28.0`. Non copiare automaticamente il vecchio extra `[serve]` da una model card: l'entry point del server è incluso nella distribuzione corrente. Le dipendenze risolte vengono registrate, non dichiarate qui come una combinazione già collaudata su M4. [S14, S16]

```bash
source "$HOME/qwen-m4-16gb/lab.env"
PY="$(brew --prefix python@3.11)/bin/python3.11"
"$PY" -m venv "$LAB/venv-tq"

"$LAB/venv-tq/bin/python" -m pip install --upgrade pip
"$LAB/venv-tq/bin/python" -m pip install "turboquant-mlx-full==0.28.0"
"$LAB/venv-tq/bin/python" -m pip check
"$LAB/venv-tq/bin/python" -m pip freeze > "$LAB/logs/tq.freeze.txt"

"$LAB/venv-tq/bin/turboquant-serve" --help > "$LAB/logs/tq-serve-help.txt"
"$LAB/venv-tq/bin/turboquant-plan" --help > "$LAB/logs/tq-plan-help.txt"
```

### 5.2 Pianifica prima di scaricare

```bash
"$LAB/venv-tq/bin/turboquant-plan" \
  --model manjunathshiva/Qwen3.6-35B-A3B-tq3a-tqTe-down4-g64 \
  --ram-gb 16 --context 8192 --kv-bits 8
```

Il planner legge metadati/header e produce una **stima**, non un test del tuo carico reale. Se segnala che il modello non entra, non ignorare il risultato. La documentazione del progetto distingue memoria resident, cache e possibili strategie di streaming: qui stiamo provando soltanto il percorso resident del checkpoint asimmetrico. [S17]

Poi, nel terminale dei download:

```bash
fetch_model manjunathshiva/Qwen3.6-35B-A3B-tq3a-tqTe-down4-g64 \
  "$LAB/models/qwen36-tq-asymmetric"
```

### 5.3 Limite wired: modifica facoltativa e temporanea, non RAM aggiuntiva

La ricetta del manutentore per il checkpoint asimmetrico su 16 GB aumenta il tetto wired a `13824` per contesti sotto circa 16K. Non è una garanzia che il tuo Mac conservi abbastanza margine per ogni carico. Non partire dalla variante 14 GiB/21K riportata per prove più spinte. [S1]

Prima ferma gli altri server e salva tutto. Leggi il valore corrente; se la chiave manca o il comando fallisce, fermati anziché applicare modifiche alternative alla cieca:

```bash
sysctl -n iogpu.wired_limit_mb

# Salva il valore prima della prima modifica, senza sovrascriverlo ai tentativi successivi.
if [ ! -f "$LAB/logs/wired_limit_before.txt" ]; then
  sysctl -n iogpu.wired_limit_mb > "$LAB/logs/wired_limit_before.txt"
fi
cat "$LAB/logs/wired_limit_before.txt"

# SOLO se accetti consapevolmente la riduzione del margine disponibile al sistema:
sudo sysctl -w iogpu.wired_limit_mb=13824
```

Non inserire la modifica in file permanenti, non disabilitare swap/SIP e non eseguire altri modelli in parallelo. Se non vuoi toccare questo parametro, resta con Bonsai e rinvia questa specifica configurazione TurboQuant.

### 5.4 Avvia l'API TurboQuant

```bash
"$LAB/venv-tq/bin/turboquant-serve" \
  --model "$LAB/models/qwen36-tq-asymmetric" \
  --host 127.0.0.1 --port 8080 \
  --kv-bits 8 --tool-syntax-greedy --disk-cache \
  --prefill-step-size 128 \
  --temp 0.7 --top-p 0.8 --top-k 20 \
  --chat-template-args '{"enable_thinking":false}' \
  --prompt-concurrency 1 \
  2>&1 | tee "$LAB/logs/tq-server.log"
```

Questo profilo segue le opzioni pubblicate dal manutentore, ma usa solo loopback. Parti dai piccoli smoke test; non dalla finestra massima del modello. Le cache e i limiti runtime automatici non rendono sicuro un numero illimitato di client. La cache su disco può conservare informazioni derivate dai prompt: usa dati sintetici, non segreti, per queste prove. [S1, S17]

### 5.5 Ferma e ripristina

Dopo **Ctrl+C** e la chiusura del server:

```bash
sudo sysctl -w "iogpu.wired_limit_mb=$(cat "$LAB/logs/wired_limit_before.txt")"
sysctl -n iogpu.wired_limit_mb
```

La ricetta upstream descrive questa modifica come per-boot. Un riavvio elimina una modifica temporanea non resa persistente; il ripristino esplicito evita comunque di lasciare attivo un tetto alterato durante altre attività. [S1]

## 6. Stesso test per i tre server

Questa sezione è una procedura proposta per il tuo laboratorio, non un benchmark ripreso da terzi.

### 6.1 Verifica l'API

Da un secondo Terminale, scegli **solo il server effettivamente avviato**:

```bash
source "$HOME/qwen-m4-16gb/lab.env"

# Binary
curl -fS http://127.0.0.1:8082/v1/models

# Oppure ternary, NON contemporaneamente al binary:
# curl -fS http://127.0.0.1:8081/v1/models

# Oppure TurboQuant:
# curl -fS http://127.0.0.1:8080/v1/models
```

Per il binary usiamo l'alias `bonsai-binary`; MLX può pubblicare il percorso assoluto del modello; la ricetta TurboQuant usa `default_model`. Verifica l'elenco anziché sostituire silenziosamente il modello con un altro. [S1, S15]

### 6.2 Esegui lo smoke test allegato

Estrai il pacchetto nella directory del laboratorio (adatta solo il percorso del file ZIP se il browser lo salva altrove):

```bash
unzip "$HOME/Downloads/Qwen_Bonsai_M4_16GB_Standalone.zip" -d "$LAB"
PROBE="$LAB/Qwen_Bonsai_M4_16GB_Standalone/smoke_test.py"
```

Dopo l'avvio del binary:

```bash
"$LAB/venv-tools/bin/python" "$PROBE" \
  --base-url http://127.0.0.1:8082/v1 --model bonsai-binary \
  --repeats 3 --out "$LAB/logs/binary-smoke.jsonl"
```

Dopo aver fermato il binary e avviato il ternary:

```bash
"$LAB/venv-tools/bin/python" "$PROBE" \
  --base-url http://127.0.0.1:8081/v1 \
  --model "$LAB/models/bonsai-ternary-175" \
  --repeats 3 --out "$LAB/logs/ternary-smoke.jsonl"
```

Dopo aver fermato il ternary e avviato TurboQuant:

```bash
"$LAB/venv-tools/bin/python" "$PROBE" \
  --base-url http://127.0.0.1:8080/v1 --model default_model \
  --repeats 3 --out "$LAB/logs/tq-smoke.jsonl"
```

Il client verifica un contratto JSON e il recupero di un dato sintetico fornito nel prompt, tre volte. Salva richieste, risposte, esiti, tempo end-to-end e `usage` se il server lo espone. Non calcola falsi token/s dividendo l'intera durata richiesta per i token generati. Il timeout è di socket, non un arresto garantito del processo inferenziale: su un timeout controlla il server prima di riprovare.

Per una verifica aggiuntiva del formato tool calling, aggiungi `--with-tools`. Il client richiede una sola chiamata `lookup_order`, ne verifica nome e argomenti e **non la esegue**. Se il test fallisce, conserva il caso: il server può essere utile per chat ma non ancora adatto a un harness agentico. Un esito positivo di questo test minimo non dimostra affidabilità su repository reali.

### 6.3 Misura memoria e velocità senza confondere le grandezze

Prima e dopo ciascuna prova:

```bash
sysctl vm.swapusage
vm_stat
```

Annota dal runtime il tempo di prefill e la velocità di decode separatamente. Una prima richiesta a freddo e una richiesta con cache calda non sono confrontabili senza dichiararlo. La memoria indicata da MLX non è automaticamente la memoria totale di macOS. Apple spiega che la pressione memoria combina diversi fattori, incluso lo swap: controlla anche il grafico in Monitoraggio Attività. [S18]

Scheda proposta per ogni modello:

| Voce | Valore da misurare sul tuo Mini |
|---|---|
| Versione macOS / runtime / SHA checkpoint | |
| Contesto effettivo misurato dal tokenizer/server | |
| Profilo thinking / sampling | |
| Prompt tokens / output tokens | |
| Tempo prefill / decode token/s | |
| Tempo totale richiesta | |
| Memoria runtime e pressione memoria macOS | |
| Swap iniziale / finale | |
| JSON / richiamo dato / tool-format | |
| Prima richiesta a freddo o cache calda | |

Per aumentare il contesto prepara prompt sintetici a 4K, poi 8K e soltanto dopo 16K, misurandoli col tokenizer o con `usage.prompt_tokens`: numero di caratteri non equivale a numero di token. Sul binary modifica `-c` al livello scelto; sui server MLX/TQ della guida la lunghezza del prompt va limitata dal client/procedura, non dal flag `--max-tokens`, che riguarda l'output. Lascia spazio all'output nella finestra totale.

Interrompi se il sistema diventa poco responsivo, la pressione memoria resta alta, lo swap cresce continuativamente, arrivano errori Metal o le risposte degenerano. Non aumentare il limite wired per nascondere questi segnali.

## 7. Troubleshooting essenziale

| Sintomo | Primo controllo |
|---|---|
| MLX non si installa | Python arm64, macOS supportato, ambiente corretto; non forzare Rosetta |
| Binary Q1_0 non riconosciuto | Versione di llama.cpp; non usare un vecchio binario senza supporto |
| Si avvia Bonsai 2 | Hai usato i wrapper generici senza famiglia; usa il percorso Q1_0 esplicito della guida |
| Packed ternary rifiutato | `model_file`, fiducia nel codice, versione del loader; non è un generico modello 2-bit |
| `unrecognized arguments: --kv-bits` in MLX server | Non presente nel server 0.31.3; non copiare flag da generate/TurboQuant |
| TQ caricato con loader normale | Usa `turboquant-serve`, non assumere che il formato sia affine MLX standard |
| Generazione senza risposta finale | Verifica profilo thinking e limite output; ispeziona risposta e log |
| Tool call soltanto descritta in prosa | Fallimento del contratto tool-format, non successo agentico |
| Tempo elevato solo al primo turno | Distingui caricamento/prefill/cache dal decode |

Le incompatibilità di formato e i flag sopra sono ricavati dalle fonti dei runtime. Le azioni diagnostiche sono indicazioni operative, non prove che ogni sintomo abbia una sola causa. [S8, S13–S17]

## 8. Cosa considero sufficiente prima di Kowalski

Richiederei tre avvii puliti del checkpoint scelto, risposte complete, log leggibili, pressione memoria sostenibile, nessuna crescita continua dello swap e passaggio dei controlli funzionali minimi. Poi costruirei un test separato di coding con sandbox e suite esterna. Non chiamerei questi smoke test un benchmark SWE o un collaudo di coding agentico.

Fra questi tre percorsi: binary è il riferimento iniziale con più margine; il ternary compatto è la prova per risparmiare memoria senza cambiare i pesi ternari di origine; TurboQuant è il candidato da esplorare per MoE/tool use, accettando un margine molto minore. L'eventuale ternary ufficiale 2-bit resta un utile confronto di velocità/semplicità. Nessuna integrazione con Kowalski è stata eseguita in questo pacchetto.

## Fonti primarie

Le fonti più specifiche sono model card, sorgenti e benchmark dei manutentori. Non rappresentano tre studi indipendenti sul medesimo Mac mini M4 16 GB.

- **S1** — TurboQuant asymmetric model card: https://huggingface.co/manjunathshiva/Qwen3.6-35B-A3B-tq3a-tqTe-down4-g64
- **S2** — Ternary Bonsai packed 1.75 bpw: https://huggingface.co/inductiveML/Ternary-Bonsai-27B-mlx-lossless-1.75bpw
- **S3** — Bonsai binary GGUF files: https://huggingface.co/prism-ml/Bonsai-27B-gguf/tree/main
- **S4** — Bonsai community benchmark register: https://github.com/PrismML-Eng/Bonsai-demo/blob/main/community-benchmarks/bonsai/README.md
- **S5** — MLX installation: https://ml-explore.github.io/mlx/build/html/install.html
- **S6** — Homebrew installation: https://docs.brew.sh/Installation
- **S7** — Hugging Face CLI: https://huggingface.co/docs/huggingface_hub/guides/cli
- **S8** — PrismML Bonsai 1 runtime/format guide: https://github.com/PrismML-Eng/Bonsai-demo/blob/main/Bonsai1_README.md
- **S9** — PrismML binary downloader: https://github.com/PrismML-Eng/Bonsai-demo/blob/main/scripts/download_binaries.sh
- **S10** — PrismML llama CLI launcher: https://github.com/PrismML-Eng/Bonsai-demo/blob/main/scripts/run_llama.sh
- **S11** — PrismML llama server launcher: https://github.com/PrismML-Eng/Bonsai-demo/blob/main/scripts/start_llama_server.sh
- **S12** — Ternel sources and verification artifacts: https://github.com/inductiveML/ternel
- **S13** — MLX-LM 0.31.3 generation CLI: https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/generate.py
- **S14** — TurboQuant package configuration: https://github.com/manjunathshiva/turboquant-mlx/blob/main/pyproject.toml
- **S15** — MLX-LM 0.31.3 server: https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/server.py
- **S16** — TurboQuant release on PyPI: https://pypi.org/project/turboquant-mlx-full/0.28.0/
- **S17** — TurboQuant runtime and memory planning: https://github.com/manjunathshiva/turboquant-mlx
- **S18** — Apple Activity Monitor memory usage: https://support.apple.com/guide/activity-monitor/view-memory-usage-actmntr1004/mac
