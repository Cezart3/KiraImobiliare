import { CONTACT_EMAIL, SITE_NAME } from '@/lib/site'
import { LegalLayout, LegalSection } from './LegalLayout'

export function TermsPage() {
  return (
    <LegalLayout title="Termeni și condiții">
      <LegalSection title="Serviciul">
        <p>
          {SITE_NAME} este un motor de căutare/agregator de anunțuri de închiriere publicate pe
          site-uri terțe din România. Nu suntem agenție imobiliară, nu intermediem tranzacții și
          nu suntem autorii anunțurilor. Fiecare anunț afișat trimite către pagina originală de pe
          site-ul sursă; corectitudinea informațiilor din anunțuri aparține autorilor și
          platformelor sursă. Informațiile derivate afișate de noi (de ex. distanța de mers pe jos
          până la un loc de parcare, marcată ca aproximativă) sunt estimări orientative.
        </p>
      </LegalSection>

      <LegalSection title="Contul">
        <p>
          Pentru funcțiile complete este necesar un cont (email + parolă sau Google). Ești
          responsabil de păstrarea confidențialității datelor de autentificare. Poți șterge
          contul oricând.
        </p>
      </LegalSection>

      <LegalSection title="Acces și plată">
        <p>
          Accesul gratuit afișează un număr limitat de anunțuri per căutare (numărul total găsit
          este întotdeauna afișat). În prima lună de la lansarea serviciului, accesul complet
          este gratuit pentru toți utilizatorii.
        </p>
        <p>
          După această perioadă, accesul complet costă <strong>15 lei și este valabil 30 de
          zile</strong>. Este o <strong>plată unică</strong>, prin Stripe — <strong>nu este
          abonament și nu se reînnoiește automat</strong>. Nu reținem nicio sumă recurentă. Când
          cele 30 de zile expiră, accesul complet se oprește, iar tu poți cumpăra din nou, manual,
          alte 30 de zile dacă dorești. Nu există alte taxe ascunse.
        </p>
      </LegalSection>

      <LegalSection title="Dreptul de retragere">
        <p>
          Conform OUG 34/2014, pentru servicii de conținut digital prestarea începe imediat după
          plată, cu acordul tău expres exprimat la finalizarea comenzii; prin urmare îți exprimi
          acordul ca accesul să înceapă imediat. Fiind o plată unică pentru o perioadă de 30 de
          zile, nu există reînnoire de oprit. Pentru orice solicitare legată de plăți scrie la {CONTACT_EMAIL}.
        </p>
      </LegalSection>

      <LegalSection title="Proprietate intelectuală și utilizare permisă">
        <p>
          Codul sursă, designul, textele, structura bazei de date și elementele derivate
          create de noi (clasificarea încălzirii și a parcării, potrivirea cu locurile de
          parcare, estimările de distanță, organizarea pe zone și repere) sunt protejate de
          dreptul de autor și aparțin {SITE_NAME}. Marca, numele și logo-ul {SITE_NAME} ne
          aparțin. © 2026 {SITE_NAME}. Toate drepturile rezervate.
        </p>
        <p>
          Este interzisă, fără acordul nostru scris: copierea, reproducerea sau crearea de
          lucrări derivate din serviciu; extragerea automată a datelor noastre (scraping,
          crawling, apeluri automate către API sau pagini); reutilizarea bazei noastre de
          date, integral sau a unei părți substanțiale. Poți folosi serviciul normal, ca
          utilizator, pentru a căuta chirii pentru tine.
        </p>
      </LegalSection>

      <LegalSection title="Limitarea răspunderii">
        <p>
          Serviciul este furnizat «ca atare». Nu garantăm că toate anunțurile existente pe piață
          apar în rezultate, că datele extrase automat (preț, zonă, parcare, încălzire) sunt
          lipsite de erori sau că serviciul este disponibil neîntrerupt. Răspunderea noastră
          totală este limitată la contravaloarea abonamentului pe ultima lună plătită.
        </p>
      </LegalSection>

      <LegalSection title="Soluționarea litigiilor">
        <p>
          Încercăm întâi rezolvarea amiabilă: {CONTACT_EMAIL}. Poți apela și la ANPC —
          Soluționarea Alternativă a Litigiilor (anpc.ro/ce-este-sal) sau la platforma europeană de
          Soluționare Online a Litigiilor (ec.europa.eu/consumers/odr). Legea aplicabilă: legea
          română.
        </p>
      </LegalSection>
    </LegalLayout>
  )
}
