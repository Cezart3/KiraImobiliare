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

      <LegalSection title="Abonamentul">
        <p>
          Accesul gratuit afișează un număr limitat de anunțuri per căutare (numărul total găsit
          este întotdeauna afișat). Abonamentul «acces complet» costă 15 lei/lună și se
          reînnoiește automat lunar prin Stripe. Poți anula oricând, în doi pași, din «Gestionează
          abonamentul» — anularea oprește reînnoirea, iar accesul rămâne activ până la finalul
          perioadei deja plătite. Nu există alte taxe ascunse.
        </p>
      </LegalSection>

      <LegalSection title="Dreptul de retragere">
        <p>
          Conform OUG 34/2014, pentru servicii de conținut digital prestarea începe imediat după
          plată, cu acordul tău expres exprimat la finalizarea comenzii; poți totuși anula oricând
          cu efect la finalul perioadei curente de facturare. Pentru orice solicitare legată de
          plăți scrie la {CONTACT_EMAIL}.
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
