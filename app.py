from GenDB import *
from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "password"

#classe per registrare info su chi logga 
class log:
    tipo = ""
    myuser = ""

@app.route("/")
def index():
    return redirect(url_for("home"))

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        mailuser = request.form["email"]
        myuser = Utente.Identifica(mailuser)

        #Se lo user che si sta loggando non è nella tabella utenti lo andiamo a ricercare nella tabella personale
        if myuser != None:
            session["myss"] = myuser.CodFiscale
        else:
            myuser = Personale.Identifica(mailuser)
            if myuser != None:
                session["myss"] = myuser.CodFiscale
            
        password = request.form["password"]

        # query che restituisce i risultati se un utente e poi staff risulta nel DB
        if(Utente.LoginUtente(mailuser,password) == True):
            log.tipo  = "utente"
            log.myuser = myuser.CodFiscale
            flash(f"Benvenuto/a {myuser.Nome}!","info")
            return redirect(url_for("area"))
        if(Personale.LoginStaff(mailuser,password) == True):
            log.tipo = "staff"
            log.myuser = myuser.CodFiscale
            flash(f"Benvenuto/a {myuser.Nome}!","info")
            return redirect(url_for("staff", ))
        else:
            #nessuno trovato + errore
            flash("Errore credenziali errate!","error")
            return render_template("login.html")
    else:
        if("myss" in session and log.tipo=="utente"):
            return redirect(url_for("area"))
        if("myss" in session and log.tipo=="staff"):
            return redirect(url_for("staff"))
        else:
            return render_template("login.html")

@app.route("/logout")
def logout():
    log.tipo = ""
    log.myuser = ""
    #slogga l'utente dal sito e quindi blocca le pagie private
    session.pop("myss", None)
    return redirect(url_for("login"))


@app.route("/area", methods=['GET', 'POST'])
def area():
    #query per estrarre le prenotazioni dell'utente loggato
    Prenot = Prenotazione.Seleziona(log.myuser)

    #gestione liste conteneti le prenotazioni degli slot e delle lezioni
    s = []
    l = []
    for i in range(0,len(Prenot)):
        if(Prenot[i].SlotId != None):
            s.append(Prenot[i].SlotId)
        else:
            l.append(Prenot[i].LezioneId)

    #liste per tenere conto di tutti gli slot e delle lezioni
    listSlot = []
    listLen = []
    
    for i in range(0,len(s)):
        listSlot.extend(Slot.Seleziona(s[i]))
        
    for i in range(0,len(l)):
        listLen.extend(Lezione.Seleziona(l[i]))

    #liste contenenti le prenotazioni del giorno odierno
    #si prendono dalle liste già formate precedentemente e si va a spostare la prenotazione 
    todaySlot = []
    todayLen = []
    
    for i in range(0,len(listSlot)):
        if listSlot[i].Data == date.today():
            todaySlot.append(listSlot[i])
    i = 0
    while i < len(listSlot):
        if listSlot[i].Data <= date.today():
            listSlot.remove(listSlot[i])
        else:
            i+=1

    for i in range(0,len(listLen)):
        if listLen[i].Data == date.today():
            todayLen.append(listLen[i])
    i = 0
    while i < len(listLen):
        if listLen[i].Data <= date.today():
            listLen.remove(listLen[i])
        else:
            i+=1

    if request.method == "POST":
        #cancello prenotazione
        Id = Prenotazione.Identifica(log.myuser,request.form['botton'])
        Prenotazione.Canc(Id)
        flash("Cancellazione avvenuta con successo!","info")
        return redirect(url_for("succes"))
    else:
        if "myss" in session and log.tipo == "utente":
            #stampa della scheda dell'utente
            SchedaUser = list(Scheda.Seleziona(log.myuser))
            Us = list(Utente.Seleziona(log.myuser))

            #check nel caso in cui la scheda fosse scaduta viene eliminata
            if SchedaUser != []:
                if Scheda.Check(SchedaUser[0].IdScheda) == true:
                    SchedaUser = list(Scheda.Seleziona(log.myuser))
                    Us = list(Utente.Seleziona(log.myuser))

            #check controllo se l'utente ha una scheda da visionare
            if len(SchedaUser) != 0 and len(Us) != 0:  
                #es della sccheda
                Es = list(Associazione.Seleziona(SchedaUser[0].IdScheda))
                #calorie totali della scheda
                Kcal = Esercizio.Calorie(SchedaUser[0].IdScheda)

                return render_template("area.html", ListaScheda = SchedaUser, LenList = len(SchedaUser),
                                        ListaEs = Es, LenEs = len(Es),
                                        User = Us, LenUser = len(Us), 
                                        Slot = listSlot, lenSlot = len(listSlot), 
                                        Lezione = listLen, lenLezioni = len(listLen),
                                        Tslot = todaySlot, lenTS = len(todaySlot),
                                        Tlen = todayLen, lenTL = len(todayLen),
                                        KcalTot = Kcal)
            else:
                if len(SchedaUser) == 0:
                    return render_template("area.html", ListaScheda = SchedaUser, LenList = len(SchedaUser), 
                                            ListaEs = [], LenEs = 0, 
                                            User = Us, LenUser = len(Us), 
                                            Slot = listSlot, lenSlot = len(listSlot), 
                                            Lezione = listLen, lenLezioni = len(listLen),
                                            Tslot = todaySlot, lenTS = len(todaySlot),
                                            Tlen = todayLen, lenTL = len(todayLen),
                                            KcalTot = 0)
                else:
                    return render_template("problem")
        else:
            return redirect(url_for("login"))

@app.route("/prenot", methods=['GET', 'POST'])
def prenot():
    if "myss" in session and log.tipo == "utente":
        data = date.today()
        if request.method == "POST":
            # questo blocco di codice permette di aggiornare la pagina delle prenotazioni con quelle della data in input
            if request.form["botton"] == "Update":
                data = request.form["data"]
                data = datetime.strptime(data, '%Y-%m-%d')
                if data < datetime.today():
                    data = date.today()
            else:
                # controllo la prenotazione non sia già stata effettuata
                if Prenotazione.Check(log.myuser,request.form["botton"]) == true:
                    Prenotazione.Inserisci(date.today(),log.myuser,request.form["botton"])
                    flash("Prenotazione avvenuta con successo!","info")
                    return redirect(url_for("succes"))
                else:
                    flash("Errore la prenotazione non è avvenuta!","error")
                    return redirect(url_for("problem"))
        
        # popolazione liste relative alle lezioni da stampare nella pagina 
        LezioniKarate = list(Lezione.Prog(1,data))
        LezioniYoga = list(Lezione.Prog(2,data))
        LezioniZumba = list(Lezione.Prog(3,data))
        LezioniPilates = list(Lezione.Prog(4,data))

        CapKarate = Corso.Cap(1)
        CapYoga = Corso.Cap(2)
        CapZumba = Corso.Cap(3)
        CapPilates = Corso.Cap(4)

        SlotPesi = list(Slot.Prog(1,data))
        SlotFitness = list(Slot.Prog(2,data))
        Pesi = list(Sala.Seleziona(1))
        Fitness = list(Sala.Seleziona(2))  

        #casting necessario per l'input value
        if type(data) == datetime:
            data = data.date()
        
        return render_template("prenot.html", lisLezioniK = LezioniKarate, lenKarate = len(LezioniKarate), 
                                lisLezioniY = LezioniYoga, lenYoga = len(LezioniYoga),
                                lisLezioniZ = LezioniZumba, lenZumba = len(LezioniZumba),
                                lisLezioniP = LezioniPilates, lenPilates = len(LezioniPilates),
                                lisSlotP = SlotPesi, lenPesi = len(SlotPesi), 
                                lisSlotF = SlotFitness, lenFitness = len(SlotFitness), 
                                dataAct = data, 
                                SalaP = Pesi, lenSalaP = len(Pesi), 
                                SalaF = Fitness, lenSalaF = len(Fitness),
                                Karate = CapKarate, Yoga = CapYoga, Zumba = CapZumba, Pilates = CapPilates)
    else:
        return redirect(url_for("login"))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #info relative ad un utente
        nome = request.form["nome"]
        cognome = request.form["cognome"]
        cf = request.form["cf"]
        sesso = request.form["sesso"]
        dataNasc = request.form["data"]
        peso = request.form["peso"]
        altezza = request.form["altezza"]
        telefono = request.form["tel"]
        email = request.form["email"]
        password = request.form["password"]
        abbonamento = request.form["abbonamento"]

        if CheckTel(telefono) == true and CheckDataNascita(dataNasc) == true and CheckCf(cf) == true:
            #IF controlla con query che non ci sia già una mail o codice fiscale uguali già registrati
            if(Utente.Controllo(email,cf) == True):
                #inserimento utente
                Utente.Inserisci(cf,cognome,nome,dataNasc,sesso,telefono,peso,altezza,email,password,abbonamento)
                flash("Registrazione avvenuta con successo!","info")
                return redirect(url_for("area"))
            else:
                return render_template("register.html")
        else:
            flash("Errore registrazione non avvenuta!","error")
            return redirect(url_for("problem"))
    else:
        return render_template("register.html")

@app.route("/esito")
def esito():
    return redirect(url_for("prenot"))

@app.route("/mex_trainer/<name>", methods=['GET', 'POST'])
def mex_trainer(name):
    if "myss" in session:
        #query che partendo dal nome si fa dare tutte le info sul personal trainer
        PersonalTrainer = Personale.Seleziona(name)
        CfPt = PersonalTrainer.CodFiscale

        if request.method == "POST":
            user = log.myuser 
            text = request.form["Text"]
            #insert sulla tabella messaggi allenatore
            Messaggio.Inserisci(text,date.today(),user,CfPt)
            flash("Messaggio inviato con successo!","info")
            return redirect(url_for("succes"))
        else:
            return render_template("mex_trainer.html",persona = PersonalTrainer)
    else:
        return redirect(url_for("login"))

@app.route("/staff", methods=['GET', 'POST'])
def staff():
    if "myss" in session and log.tipo == "staff":
        check = Personale.Staff(log.myuser) #controllo ruolo del personale
        if request.method == 'POST':
            #cancellazione membro staff
            Personale.Delate(request.form['botton'])
            flash("Eliminazione avvenuta correttamente!","info")
            return redirect(url_for("succes"))
        return render_template("staff.html", access = check)
    else:
        return redirect(url_for("login"))

@app.route("/succes")
def succes():
    return render_template("succes.html")

@app.route("/problem")
def problem():
    return render_template("problem.html")

@app.route("/QRdoccia")
def QRdoccia():
    if("myss" in session and log.tipo == "utente"):
        return render_template("QRdoccia.html")
    else:
        return redirect(url_for("login"))

@app.route("/QRCassette")
def QRCassette():
    if("myss" in session and log.tipo == "utente"):
        return render_template("QRCassette.html")
    else:
        return redirect(url_for("login"))

@app.route("/mex")
def mex():
    if("myss" in session and log.tipo == "staff"):
        #lista di tutti i messaggi
        MexList = list(Messaggio.Seleziona(log.myuser))
        return render_template("mex.html", LMex = MexList, LenMex = len(MexList))
    else:
        return redirect(url_for("login"))

@app.route("/new_member", methods=['GET', 'POST'])
def new_member():
    if("myss" in session and log.tipo == "staff"):
        if request.method == "POST":
            # dati nuovo utente
            nome = request.form["nome"]
            cognome = request.form["cognome"]
            cf = request.form["cf"]
            sesso = request.form["sesso"]
            dataNasc = request.form["data"]
            peso = request.form["peso"]
            altezza = request.form["altezza"]
            telefono = request.form["tel"]
            email = request.form["email"]
            password = request.form["password"]
            specializzazione = request.form["specializzazione"]
            ruolo = request.form["ruolo"]

            # controlli effettuti nel genDB per i parametri telefono, dataNasc e cf
            if CheckTel(telefono) == true and CheckDataNascita(dataNasc) == true and CheckCf(cf) == true:
                if(Personale.Controllo(email,cf) == True):
                    #inserimento nuovo utente nel DB
                    Personale.Inserisci(cf,cognome,nome,dataNasc,sesso,telefono,peso,altezza,email,password,ruolo,specializzazione)
                    flash("Inserimento avvenuto corettamente!","info")
                    return redirect(url_for("login"))
                else:
                    # già presente
                    flash("Personale già registrato!","error")
                    return render_template("new_member.html")
            else:
                # altri errori
                flash("Operazione fallità, errore di inserimento!","error")
                return redirect(url_for("problem"))
        else:
                return render_template("new_member.html")
    else:
        return redirect(url_for("login"))

@app.route("/gestionepalestra", methods=['GET', 'POST'])
def gestionepalestra():
    if("myss" in session and log.tipo == "staff"):
        if request.method == "POST":
            # controllo dell'identificatore assegnato al bottone, D delete del corso oppure U per Update della capienza massima di un corso, P per aggiornare capienza della sala pesi, F per aggiornare la capienza della sala fintness
            utility = request.form["botton"]
            if utility != []:
                if utility[0] == "D":
                    #cancellazione corso
                    Corso.Delete(request.form["botton"])
                    flash("Cancellazione avvenuata con successo!","info")
                    return redirect(url_for("succes"))
                elif utility[0] == "U":
                    #aggiornamento corso
                    Corso.Update(utility,request.form["Capienza"])
                    flash("Aggiornamento avvenuto con successo!","info")
                    return redirect(url_for("succes"))
                elif utility[0] == "P":
                    #aggiornamento sala pesi
                    Sala.Update(request.form["botton"],request.form["npesi"])
                    flash("Aggiornamento avvenuto con successo!","info")
                    return redirect(url_for("succes"))
                else:
                    #aggiornamento sala fitnes
                    Sala.Update(request.form["botton"],request.form["nfit"])
                    flash("Aggiornamento avvenuto con successo!","info")
                    return redirect(url_for("succes"))
        else:
            CapPesi = Sala.Cap(1)
            CapFit = Sala.Cap(2)

            corsi = Corso.SelezionaCorsi()
            
            return render_template("gestionepalestra.html", Pesi = CapPesi,
                                               Fit = CapFit,
                                               corso = corsi,
                                               lenCorsi = len(corsi))
    else:
        return redirect(url_for("login"))

@app.route("/aggiornadati", methods=['GET', 'POST'])
def aggiornadati():
    if "myss" in session and log.tipo == "utente":
        Us = Utente.Seleziona(log.myuser)
        if request.method == "POST":
            #dati per aggiornamento
            nome = request.form["nome"]
            cognome = request.form["cognome"]
            cf = request.form["cf"]
            sex = request.form["sesso"]
            dataNasc = request.form["data"]
            peso = request.form["peso"]
            altezza = request.form["altezza"]
            telefono = request.form["tel"]
            email = request.form["email"]
            oldpassword = request.form["oldpassword"]
            newpassword = request.form["newpassword"]
            abbonamento = request.form["abbonamento"]

            #metodi nel genDB che controllano gli atributi
            if CheckTel(telefono) == true and CheckDataNascita(dataNasc) == true and CheckCf(cf) == true and email != None and newpassword != None:
                #controllo old password sia giusta
                if(Utente.LoginUtente(Us[0].Mail,oldpassword)):
                    #aggiornamento effettivo 
                    Utente.Update(Us[0].CodFiscale,nome,cognome,cf,sex,dataNasc,peso,altezza,telefono,email,newpassword,abbonamento)
                    flash("Aggiornamento avvenuto con successo!","info")
                    return redirect(url_for("logout"))
                else:
                    # messaggio di errore oldpassword falsa
                    flash("La password inserita non coincide con la vecchia password!","error")
                    return render_template("aggiornadati.html", User = Us)    
            else:
                flash("Errore inserimento dati!","error")
                return redirect(url_for("problem"))
        else:
            return render_template("aggiornadati.html", User = Us)
    else:
        return redirect(url_for("login"))  

@app.route("/scheda", methods=['GET', 'POST'])
def scheda():
    if "myss" in session and log.tipo == "staff":
        Us = Utente.SenzaScheda()
        if request.method == "POST":
            #info riguardati la scheda
            User = request.form["utente"]
            Tipo = request.form["tipo"]
            Dif = request.form["difficoltà"]
            Nr = int(request.form["nallenamenti"])
            DataInizio = request.form["dataInizio"]
            DataFine = request.form["dataFine"]
            NrEs = int(request.form["nes"])

            try:
                Scheda.Inserisci(Tipo,Dif,Nr,DataInizio,DataFine,User,log.myuser)
            except:
                flash("Errore inserimento scheda, dati non validi", "error")
                return redirect(url_for("problem"))


            ScId = Scheda.Identifica(User)
            Eserc = Esercizio.Seleziona()
            Ut = Scheda.User(ScId)

            return render_template("esercizi.html", SchedaAc = ScId, 
                                                    User = Ut, 
                                                    Es = Eserc, lenEs = len(Eserc), 
                                                    Nes = NrEs)
        else:
            return render_template("scheda.html", Users = Us, lenUsers = len(Us))
    else:
        return redirect(url_for("login"))  

@app.route("/esercizi", methods=['GET', 'POST'])
def esercizi():
    if "myss" in session and log.tipo == "staff":
        if request.method == "POST":
            #gestione della creazione di una scheda
            Id = request.form["Id"]
            NrEs = int(request.form["nes"])

            Occ = []    #array delle occorrenze
            Es = []    #array degli esercizi interessati
            Rip = []    #array delle ripetizioni per esercizio

            for i in range(0,11): 
                Occ.append(0)

            for i in range(NrEs):
                Es.append(int(request.form["esercizio"+str(i)]))
                Rip.append(int(request.form["rip"+str(i)]))

            for i in range(NrEs):
                Occ[Es[i]-1] += Rip[i]

            for i in range(0,11):
                if(Occ[i] > 0):
                    # inserimento nella tabella di mezzo della n:n, degli esercizi con le relative ripetizioni
                    Associazione.Inserisci(Id,i+1,Occ[i])
                    
            flash("Scheda creata con successo!","info")
            return redirect(url_for("succes"))
        else:
            flash("Errore scehda non creata!","error")
            return render_template("esercizi.html")
    else:
        return redirect(url_for("login"))

@app.route("/nuovocorso", methods=['GET', 'POST'])
def nuovocorso():
    if "myss" in session and log.tipo == "staff":
        if request.method == "POST":
            #info sul nuovo corso
            Nome = request.form["nome"]
            NumLezioni = request.form["numLezioni"]
            CapMax = request.form["capMax"]
            LivDif = request.form["dif"]
            Ist = request.form["istruttore"]

            if Corso.Check(Nome,Ist) == true:
                #inserimento del nuovo corso
                Corso.Inserisci(Nome,NumLezioni,CapMax,LivDif,Ist)
                flash("Nuovo corso aggiunto!","info")
                return redirect(url_for("succes"))
            else:
                flash("Corso già presente","error")
                return redirect(url_for("problem"))
        else:
            #selezione del personale con ruolo di PersonalTrainer
            PersonalTrainer = Personale.SelPersonalTrainer()
            return render_template("nuovocorso.html", Ist = PersonalTrainer, lenIst = len(PersonalTrainer))
    else:
        return redirect(url_for("login"))

@app.route("/gestionepersonale", methods=['GET', 'POST'])
def gestionepersonale():
    if request.method == "POST":
        return redirect(url_for("succes"))
    else:
        #mi faccio dare la lista di tutte le persone del personale con ruolo di Personal Trainer
        personal = Personale.SelPersonalTrainer()
        return render_template("gestionepersonale.html", dip = personal, lenDip = len(personal))

if __name__ == "__main__":
    app.run(debug=True)

