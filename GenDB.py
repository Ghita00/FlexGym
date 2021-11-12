from datetime import date, datetime
from flask import Flask
import re
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship

app = Flask(__name__)

engine = create_engine('postgresql://postgres:progbasi@localhost/progbasi_database', echo=True)

Base = declarative_base() 

Session = sessionmaker(bind=engine)       # creazione della factory
session = Session()

#Funzioni globali necessarie per i controlli effettuati nel DataBase:
#funzione che data una stringa restituisce la stringa in maiuscolo
def UpperCase(Stringa):
    return Stringa.upper()

#funzione che controlla la lunghezza del numero di telefono passato
def CheckTel(Tel):
    if len(Tel) == 10:
        return true
    else:
        return false

#funzione che controlla se il codice fiscale è ben formato, presa da internet 
def CheckCf(codice_fiscale):
    CODICE_REGEXP = "^[0-9A-Z]{16}$"
    SETDISP = [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20,
        11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23 ]
    ORD_ZERO = ord('0')
    ORD_A = ord('A')

    if 0 == len(codice_fiscale):
        return false
    if(16 != len(codice_fiscale)):
        return false
    codice_fiscale = codice_fiscale.upper()
    match = re.match(CODICE_REGEXP, codice_fiscale)
    if not match:
        return false
    s = 0
    for i in range(1,14,2):
        c = codice_fiscale[i]
        if c.isdigit():                
            s += ord(c) - ORD_ZERO
        else:
            s += ord(c) - ORD_A
    for i in range(0,15,2):
        c = codice_fiscale[i]
        if c.isdigit():
            c = ord(c) - ORD_ZERO
        else:
            c = ord(c) - ORD_A
        s += SETDISP[c]
    if (s % 26 + ORD_A != ord(codice_fiscale[15])):
        return false
    return true

#funzione che controlla se la data di nascita è valida rispetto alle politiche della palestra
def CheckDataNascita(Data):
    anno = int(Data[0:4])
    if anno < (datetime.now().year - 16):
        return true
    else:
        return false

#Definizione effettiva del DataBase

class Utente(Base):
    __tablename__ = 'Utente'

    CodFiscale = Column(String(16), primary_key = True)
    Cognome = Column(String(200), nullable=False)
    Nome = Column(String(200), nullable=False)
    DataNascita = Column(Date, nullable=False)
    Sesso = Column(String(1), nullable=False)
    Telefono = Column(String(10), nullable=False)
    Peso = Column(Float)
    Altezza = Column(Float)
    Mail = Column(String(200), nullable=False)
    Password = Column(String(200), nullable=False)

    #Uno-Molti con Abbonamento
    AbbonamentoId = Column(Integer, ForeignKey('Abbonamento.IdAbbonamento', ondelete='CASCADE'))
    Abbonamento = relationship('Abbonamento', back_populates='Utente')

    #Uno-Molti con Messaggio
    Messaggio = relationship('Messaggio', back_populates='Utente', cascade="all, delete-orphan")

    #Uno-Molti con Prenotazione
    Prenotazione = relationship('Prenotazione', back_populates='Utente')

    #Uno-Uno con scheda
    Scheda = relationship("Scheda", back_populates="Utente", uselist=False)

    #controllo l'utente non risulta già registrato con medesima mail e codice fiscale
    def Controllo(Newmail,NewCF):
        NewCF = UpperCase(NewCF)
        if(session.query(Utente).filter(Utente.Mail == Newmail).count() == 0 and session.query(Utente).filter(Utente.CodFiscale == NewCF).count() == 0):
            return True
        else:
            return False

    #inserimento del nuovo utente
    def Inserisci(NewCF,NewCogn,NewNome,NewData,NewSex,NewTel,NewPeso,NewAlt,Newmail,Newpass,Newabb):
        NewCF = UpperCase(NewCF)
        Newpass = generate_password_hash(Newpass, method='pbkdf2:sha256')
        data = Utente(CodFiscale = NewCF,Cognome = NewCogn,Nome = NewNome,DataNascita = NewData,Sesso = NewSex,Telefono = NewTel,Peso = NewPeso,Altezza = NewAlt,Mail = Newmail,Password = Newpass,AbbonamentoId = Newabb)
        session.add(data)
        session.commit() 

    #controllo password inserita nel login coincida con l'hash della password presente nel DataBase
    def LoginUtente(FormMail, FormPassword):
        pwhash = session.query(Utente.Password).filter(Utente.Mail == FormMail).first()
        if pwhash != None:
            check = check_password_hash(pwhash[0], FormPassword)
            return check
        else:
            return false

    #selezione di un utente per codice fiscale
    def Seleziona(cf):
        user = session.query(Utente).filter(cf == Utente.CodFiscale)
        return user

    #selezione del primo utente per mail
    def Identifica(MailUser):
        Cf = session.query(Utente).filter(MailUser == Utente.Mail).first()
        return Cf

    #aggiornamento dei campi
    def Update(Vcf,Unome,Ucognome,Ucf,Usesso,Udata,Upeso,Ualtezza,Utelefono,Umail,Upas,Uabbonamento):
        Upas = generate_password_hash(Upas, method='pbkdf2:sha256')
        session.query(Utente).filter(Utente.CodFiscale == Vcf).update({"CodFiscale" : Ucf, "Nome" : Unome, "Cognome" : Ucognome, "DataNascita" : Udata, "Sesso" : Usesso, "Peso" : Upeso, "Altezza" : Ualtezza, "Telefono" : Utelefono, "Mail" : Umail, "Password" : Upas, "AbbonamentoId" : Uabbonamento})
        session.commit()

    #ricerca di utenti sprovvisti di di scheda di allenamento
    def SenzaScheda():
        sub = session.query(Scheda.IdUtente)
        Users = list(session.query(Utente.CodFiscale,Utente.Nome,Utente.Cognome).filter(Utente.CodFiscale.notin_(sub)))
        return Users


class Personale(Base):
    __tablename__ = 'Personale'

    CodFiscale = Column(String(16), primary_key = True)
    Cognome = Column(String(200), nullable=False)
    Nome = Column(String(200), nullable=False)
    DataNascita = Column(Date, nullable=False)
    Sesso = Column(String(1), nullable=False)
    Telefono = Column(String(10), nullable=False)
    Peso = Column(Float)
    Altezza = Column(Float)
    Mail = Column(String(200), nullable=False)
    Password = Column(String(200), nullable=False)
    Ruolo = Column(String(200))
    Specializzazione = Column(String(200))

    #Uno-Molti con Corso
    Corso = relationship('Corso', back_populates='Personale')

    #Uno-Molti con Scheda
    Scheda = relationship('Scheda', back_populates='Personale')

    #Uno-Molti con Messaggio
    Messaggio = relationship('Messaggio', back_populates='Personale', cascade="all, delete-orphan")

    #controllo se un personale non sia già registrato con medesima mail e codice fiscale
    def Controllo(Newmail,NewCF):
        NewCF = UpperCase(NewCF)
        if(session.query(Personale).filter(Personale.Mail == Newmail).count() == 0 or session.query(Personale).filter(Personale.CodFiscale == NewCF).count() == 0):
            return True
        else:
            return False

    #inserimento effettivo del nuovo membro del personale
    def Inserisci(NewCF,NewCogn,NewNome,NewData,NewSex,NewTel,NewPeso,NewAlt,Newmail,Newpass,NewRuolo,NewSpecializzazione):
        NewCF = UpperCase(NewCF)
        Newpass = generate_password_hash(Newpass, method='pbkdf2:sha256')
        data = Personale(CodFiscale = NewCF,Cognome = NewCogn,Nome = NewNome,DataNascita = NewData,Sesso = NewSex,Telefono = NewTel,Peso = NewPeso,Altezza = NewAlt,Mail = Newmail,Password = Newpass, Ruolo = NewRuolo, Specializzazione = NewSpecializzazione)
        session.add(data)
        session.commit() 

    #controllo se la password inserita coincide con la password criptata associata a quella mail nel DataBase
    def LoginStaff(MailForm,PasswordForm):
        pwhash = session.query(Personale.Password).filter(Personale.Mail == MailForm).first()
        if pwhash != None:
            check = check_password_hash(pwhash[0], PasswordForm)
            return check
        else:
            return false

    #selezione di un personale per mail
    def Identifica(MailUser):
        Cf = session.query(Personale).filter(MailUser == Personale.Mail).first()
        return Cf

    #selezione di un personale per nome
    def Seleziona(NomeURL):
        User = session.query(Personale).filter(NomeURL == Personale.Nome).first()
        if User != None:
            return User
        else:
            return None

    #controllo se un personale appartiene allo staff
    def Staff(Cod):
        rul = list(session.query(Personale.Ruolo).filter(Cod == Personale.CodFiscale))
        if(rul[0].Ruolo == "Staff"):
            return True
        else:
            return False    

    #raccolta della lista intera di PersonalTrainer
    def SelPersonalTrainer():
        data = list(session.query(Personale).filter(Personale.Ruolo == "PersonalTrainer"))
        return data

    #cancellazione di una persona dal personale
    def Delate(id):
        session.query(Personale).filter(Personale.CodFiscale == id).delete()
        session.commit()
   

class Messaggio(Base):
    __tablename__ = 'Messaggi'

    IdMessaggio = Column(Integer, primary_key=True)
    Testo = Column(Text)
    Data = Column(Date)

    #Uno-Molti con Utente
    Mittente = Column(String(16), ForeignKey('Utente.CodFiscale', ondelete='CASCADE'))
    Utente = relationship('Utente', back_populates='Messaggio')

    #Uno-Molti con Personale
    Destinatario = Column(String(16), ForeignKey('Personale.CodFiscale', ondelete='CASCADE'))
    Personale = relationship('Personale', back_populates='Messaggio')

    #inserimento di un nuovo messaggio
    def Inserisci(NewTesto, NewDate, NewMit, NewDest):
        data = Messaggio(Testo = NewTesto, Data = NewDate, Mittente = NewMit, Destinatario = NewDest)
        session.add(data)
        session.commit()

    #selezione delle informazioni principali riguardati un messaggio
    def Seleziona(Staff):
        Mex = session.query(Utente.Nome, Utente.Cognome, Utente.Telefono, Utente.Mail, Messaggio.Testo, Messaggio.Data).join(Utente).filter(Staff == Messaggio.Destinatario).order_by(Messaggio.Data)
        return Mex

class Abbonamento(Base):
    __tablename__ = 'Abbonamento'

    IdAbbonamento = Column(Integer, primary_key=True)
    Tipo = Column(String(200), nullable=False)
    Prezzo = Column(Float, nullable=False)

    #Uno-Molti con Utente
    Utente = relationship('Utente', back_populates='Abbonamento', cascade="all, delete-orphan")

class Associazione(Base):
    __tablename__ = 'Associazione'

    SchedaId = Column(ForeignKey('Scheda.IdScheda', ondelete='CASCADE'), primary_key=True)
    EsercizioId = Column(ForeignKey('Esercizio.IdEsercizio', ondelete='CASCADE'), primary_key=True)
    Ripetizioni = Column(Integer)

    Esercizio = relationship('Esercizio', back_populates='Scheda')
    Scheda = relationship('Scheda', back_populates='Esercizio')

    #selezione degli esercizi e le relative ripetizioni
    def Seleziona(SchedaId):
        Es = session.query(Esercizio.Nome, Esercizio.Corpo, Associazione.Ripetizioni, Esercizio.ApportoCalorico, Esercizio.Esecuzione).join(Esercizio).filter(SchedaId == Associazione.SchedaId)
        return Es

    #inserimento di nuove associazioni tra esercizi e schede
    def Inserisci(ScId, EsId, Rip):
        data = Associazione(SchedaId = ScId, EsercizioId = EsId, Ripetizioni = Rip)
        session.add(data)
        session.commit()

class Scheda(Base):
    __tablename__ = 'Scheda'

    IdScheda = Column(Integer, primary_key=True)
    TipoAllenamento = Column(String(200))
    LivelloDifficoltà = Column(Integer)
    AllenamentiSettimanali = Column(Integer)
    DataInizio = Column(Date, nullable=False)
    DataFine = Column(Date)

    #Uno-Uno con utente
    IdUtente = Column(String(16), ForeignKey('Utente.CodFiscale', ondelete='CASCADE'))
    Utente = relationship('Utente', back_populates='Scheda')

    #Uno-Molti con Personale
    IdPersonalTrainer = Column(String(16),ForeignKey('Personale.CodFiscale', ondelete='CASCADE'))
    Personale = relationship('Personale', back_populates='Scheda')

    #Molti-Molti con Esercizio
    Esercizio = relationship('Associazione', back_populates='Scheda', cascade="all, delete-orphan")

    #selezione delle informazioni fondamentali riguardanti una scheda
    def Seleziona(User):
        SchedaUser = session.query(Scheda.IdScheda, Scheda.TipoAllenamento, Scheda.LivelloDifficoltà, Scheda.AllenamentiSettimanali, Scheda.DataInizio, Scheda.DataFine, Personale.Nome, Personale.Cognome).join(Personale).filter(Scheda.IdUtente == User)
        return SchedaUser

    #inseirmento di una nuova scheda
    def Inserisci(TipoAl,Difficoltà,NrSet,DataI,DataF,User,Allenatore):
        data = Scheda(TipoAllenamento = TipoAl,LivelloDifficoltà = Difficoltà, AllenamentiSettimanali = NrSet, DataInizio = DataI, DataFine = DataF, IdUtente = User, IdPersonalTrainer = Allenatore)
        session.add(data)
        session.commit()
    
    #selezione di una scheda per codice fiscale dell'utente 
    def Identifica(User):
        IdSc = list(session.query(Scheda.IdScheda).filter(User == Scheda.IdUtente))
        return IdSc[0].IdScheda

    #selezione di una utente per id della scheda
    def User(Id):
        Us = list(session.query(Scheda.IdUtente).filter(Id == Scheda.IdScheda))
        if Us == []:
            return 0
        else:
            return Us[0].IdUtente

    #controllo se la validità della scheda è scaduta, in tal caso cancellazione della stessa
    def Check(Id):
        Fine = list(session.query(Scheda.DataFine).filter(Scheda.IdScheda == Id))
        if Fine[0].DataFine <= date.today():
            session.query(Scheda).filter(Scheda.IdScheda == Id).delete()
            session.commit()
            return true
        else:
            return false


class Esercizio(Base):
    __tablename__ = 'Esercizio'

    IdEsercizio = Column(Integer, primary_key=True)
    Nome = Column(String(200), nullable=False)
    Corpo = Column(String(200))
    ApportoCalorico = Column(Float)
    Esecuzione = Column(String(200))


    #Molti-Molti con Scheda
    Scheda = relationship('Associazione', back_populates='Esercizio', cascade="all, delete-orphan")

    #selezione degli esercizi presenti nel DataBase
    def Seleziona():
        q = session.query(Esercizio)
        return list(q)

    #somma del apporto calorico totale di una scheda
    def Calorie(Id):
        Kcal = list(session.query(func.sum(Esercizio.ApportoCalorico).label("CalTot")).join(Associazione).join(Scheda).filter(Scheda.IdScheda == Id).group_by(Scheda.IdScheda))
        return int(Kcal[0].CalTot)

class Corso(Base):
    __tablename__ = 'Corso'

    IdCorso = Column(Integer, primary_key=True)
    Nome = Column(String(200), nullable=False)
    NumLezioni = Column(Integer, nullable=False)
    CapienzaMax = Column(Integer, nullable=False)
    LivelloDifficoltà = Column(Integer, nullable=False)

    #Uno-Molti con Personale
    Istruttore = Column(String(16), ForeignKey('Personale.CodFiscale', ondelete='CASCADE'))
    Personale = relationship('Personale', back_populates='Corso')

    #Uno-Molti con Lezione
    Lezione = relationship('Lezione', back_populates='Corso', cascade="all, delete-orphan")

    #inserimento di un nuovo corso
    def Inserisci(NewNome,NewLez,NewCap,NewDif,NewIst):
        data = Corso(Nome = NewNome, NumLezioni = NewLez, CapienzaMax = NewCap, LivelloDifficoltà = NewDif, Istruttore = NewIst)
        session.add(data)
        session.commit()

    #cancellazione di un corso esistente 
    def Delete(Id):
        Id = int(Id[1:])
        session.query(Corso).filter(Corso.IdCorso == Id).delete()
        session.commit()

    #selezione delle principali informazioni di un corso
    def SelezionaCorsi():
        data = list(session.query(Corso.IdCorso,Corso.Nome,Corso.NumLezioni,Corso.CapienzaMax,Corso.LivelloDifficoltà,Personale.Nome.label("NomeIst"),Personale.Cognome).join(Personale))
        return data

    #aggiornamento della capienza massima di un corso
    def Update(Id,Cap):
        Id = int(Id[1:])
        session.query(Corso).filter(Corso.IdCorso == Id).update({"CapienzaMax" : Cap})
        session.commit()

    #selezione della capienza massima di un corso dato il suo Id
    def Cap(Id):
        Cap = list(session.query(Corso.CapienzaMax).filter(Corso.IdCorso == Id))
        if Cap == []:
            return 0
        else:
            return int(Cap[0].CapienzaMax)

    #controllo se un corso con medesimo nome e istruttore non esita già nel DataBase, per evitare rindondanze
    def Check(Nome, Ist):
        check = session.query(Corso).filter(Corso.Nome == Nome).filter(Corso.Istruttore == Ist).count()
        if check == 0:
            return true
        else:
            return false
        


class Lezione(Base):
    __tablename__ = 'Lezione'

    IdLezione = Column(Integer, primary_key=True)
    Data = Column(Date, nullable=False)
    Ora = Column(Time, nullable=False)
    PostiOcc = Column(Integer, default=0)

    #Uno-Molti con Corso
    CorsoId = Column(Integer, ForeignKey('Corso.IdCorso', ondelete='CASCADE'))
    Corso = relationship('Corso', back_populates='Lezione')

    #Uno-Molti con Prenotazione
    Prenotazione = relationship('Prenotazione', back_populates='Lezione', cascade="all, delete-orphan")

    #selezione delle lezioni per corso e data
    def Prog(IdCorso, date):
        lez = session.query(Lezione).filter(IdCorso == Lezione.CorsoId).filter(Lezione.Data == date)
        return lez

    #selezione dei posti occupati per id lezione
    def NumPosti(Id):
        num = list(session.query(Lezione.PostiOcc).filter(Id == Lezione.IdLezione))
        if num == []:
            return 0
        else:
            return int(num[0].PostiOcc)

    #selezione delle informazioni riguardati una lezione dato il suo Id
    def Seleziona(Id):
        lezione = list(session.query(Lezione).filter(Id == Lezione.IdLezione))
        return lezione

   
class Prenotazione(Base):
    __tablename__ = 'Prenotazione'

    IdPrenotazione = Column(Integer, primary_key=True)

    Data = Column(Date, nullable=False)

    #Uno-Molti con Utente
    UtenteId = Column(String(16), ForeignKey('Utente.CodFiscale', ondelete='CASCADE'))
    Utente = relationship('Utente', back_populates='Prenotazione')

    #Uno-Molti con Lezione
    LezioneId = Column(Integer, ForeignKey('Lezione.IdLezione', ondelete='CASCADE'))
    Lezione = relationship('Lezione', back_populates='Prenotazione')

    #Uno-Molti con Slot
    SlotId = Column(Integer, ForeignKey('Slot.IdSlot', ondelete='CASCADE'))
    Slot = relationship('Slot', back_populates='Prenotazione')

    #controllo se la prenotazione passata per id non sia già stata effettuata
    def Check(user, id):
        if(id[0] == "S"):
            id = int(id[1:])
            if session.query(Prenotazione).filter(Prenotazione.SlotId == id).filter(Prenotazione.UtenteId == user).count() == 0:
                return true
            else:
                return false
        else:
            id = int(id[1:])
            if session.query(Prenotazione).filter(Prenotazione.LezioneId == id).filter(Prenotazione.UtenteId == user).count() == 0:
                return true
            else:
                return false

    #inserimento di una nuova prenotazione andando a rimuovere il primo carattere dal iden in quanto usato per identificare se la prenotazione riguarda uno Slot o una Lezione  
    def Inserisci(date, user, iden):
        if(iden[0] == "S"): 
            iden = int(iden[1:])
            data = Prenotazione(Data = date, UtenteId = user,SlotId = iden)
            nr = Slot.NumPosti(iden)
            session.query(Slot).filter(Slot.IdSlot == iden).update({"PostiOcc" : nr+1})
        else:
            iden = int(iden[1:])
            data = Prenotazione(Data = date, UtenteId = user, LezioneId = iden)
            nr = Lezione.NumPosti(iden)
            session.query(Lezione).filter(Lezione.IdLezione == iden).update({"PostiOcc" : nr+1})
        session.add(data)
        session.commit()

    #selezione di una prenotazione per id utente
    def Seleziona(us):
        user = session.query(Prenotazione.SlotId, Prenotazione.LezioneId).filter(us == Prenotazione.UtenteId)
        return list(user)

    #selezione del'id di una prenotazione dato l'utente ed un identificativo al quale andiamo a togliere il primo carattere che distingue le prenotazioni su slot dalle prenotazioni su lezioni
    def Identifica(User, Id):
        if Id[0] == "S":
            Id = int(Id[1:])
            Id = list(session.query(Prenotazione.IdPrenotazione).filter(Id == Prenotazione.SlotId).filter(Prenotazione.UtenteId == User))
            return Id[0].IdPrenotazione
        else:
            Id = int(Id[1:])
            Id = list(session.query(Prenotazione.IdPrenotazione).filter(Id == Prenotazione.LezioneId).filter(Prenotazione.UtenteId == User))
            return Id[0].IdPrenotazione
    
    #cancellazione di una prenotazione esistente con conseguente aggiornamento del campo postiOccupati rispettivamente in slot o lezioni
    def Canc(Id):
        check = list(session.query(Prenotazione.LezioneId).filter(Id == Prenotazione.IdPrenotazione))
        if check != []:
            if check[0].LezioneId != None:
                lez = list(session.query(Prenotazione.LezioneId).filter(Id == Prenotazione.IdPrenotazione))
                num = list(session.query(Lezione.PostiOcc).filter(Lezione.IdLezione == lez[0].LezioneId))
                session.query(Lezione).filter(Lezione.IdLezione == lez[0].LezioneId).update({"PostiOcc" : num[0].PostiOcc - 1})
            else:
                slot = list(session.query(Prenotazione.SlotId).filter(Id == Prenotazione.IdPrenotazione))
                num = list(session.query(Slot.PostiOcc).filter(Slot.IdSlot == slot[0].SlotId))
                session.query(Slot).filter(Slot.IdSlot == slot[0].SlotId).update({"PostiOcc" : num[0].PostiOcc - 1})

            session.query(Prenotazione).filter(Id == Prenotazione.IdPrenotazione).delete()
            session.commit()


class Slot(Base):
    __tablename__ = 'Slot'

    IdSlot = Column(Integer, primary_key=True)
    Data = Column(Date, nullable=False)
    OraInizio = Column(Time, nullable=False)
    OraFine = Column(Time, nullable=False)
    PostiOcc = Column(Integer, default=0)

    #Uno-Molti con Prenotazione
    Prenotazione = relationship('Prenotazione', back_populates='Slot', cascade="all, delete-orphan")

    #Uno-Molti con Sala
    SalaId = Column(Integer, ForeignKey('Sala.IdSala', ondelete='CASCADE'))
    Sala = relationship('Sala', back_populates='Slot')

    #selezione degli slot per id sala e data
    def Prog(IdSala, date):
        sl = session.query(Slot).filter(IdSala == Slot.SalaId).filter(Slot.Data == date).order_by(Slot.IdSlot)
        return sl

    #selezione dei numeri di posti occupati da uno slot
    def NumPosti(Id):
        num = list(session.query(Slot.PostiOcc).filter(Id == Slot.IdSlot))
        return int(num[0].PostiOcc)

    #selezione di uno slot dato l'id di uno slot
    def Seleziona(Id):
        slot = list(session.query(Slot).filter(Id == Slot.IdSlot))
        return slot


class Sala(Base):
    __tablename__ = 'Sala'

    IdSala = Column(Integer, primary_key=True)
    Tipologia = Column(String(200), nullable=False)
    CapienzaMax = Column(Integer, nullable=False)

    #Uno-Molti con Slot
    Slot = relationship('Slot', back_populates='Sala', cascade="all, delete-orphan")

    #selezione delle informazioni di una sala dato l'id di una sala
    def Seleziona(Id):
        Data = session.query(Sala).filter(Sala.IdSala == Id)
        return Data

    #selezione della capienza massima di uno slot
    def Cap(Id):
        Cap = list(session.query(Sala.CapienzaMax).filter(Sala.IdSala == Id))
        if Cap == []:
            return 0
        else:
            return int(Cap[0].CapienzaMax)

    #aggiornamento del campo capienza massima di un dato slot
    def Update(Id,Cap):
        Id = int(Id[1:])
        session.query(Sala).filter(Sala.IdSala == Id).update({"CapienzaMax" : Cap})
        session.commit()

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True)



