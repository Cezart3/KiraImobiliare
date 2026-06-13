import { CONTACT_EMAIL, SITE_NAME } from '@/lib/site'
import { LegalLayout, LegalSection } from './LegalLayout'

export function TermsPage() {
  return (
    <LegalLayout title="Termeni și condiții">
      <LegalSection title="Ce este aplicația">
        <p>
          {SITE_NAME} este un instrument gratuit, open-source, care rulează local pe calculatorul
          tău și agregă anunțuri de închiriere publicate pe site-uri terțe din România. Nu suntem
          agenție imobiliară, nu intermediem tranzacții și nu suntem autorii anunțurilor. Fiecare
          anunț trimite către pagina originală de pe site-ul sursă; corectitudinea informațiilor
          aparține autorilor și platformelor sursă. Informațiile derivate (de ex. distanța de mers
          pe jos, marcată ca aproximativă) sunt estimări orientative.
        </p>
      </LegalSection>

      <LegalSection title="Gratuit, doar pentru uz personal local">
        <p>
          Aplicația este gratuită pentru uz personal. Nu necesită cont, nu colectează date pe un
          server al nostru și nu există nicio plată. Tot ce salvezi (favorite, preferințe) rămâne
          în browserul tău. Codul îți este pus la dispoziție ca să-l rulezi local, pentru tine —
          nu pentru a-l redistribui public sau a face bani din el (vezi secțiunea „Licență").
        </p>
      </LegalSection>

      <LegalSection title="Responsabilitatea ta când rulezi aplicația">
        <p>
          {SITE_NAME} accesează paginile publice ale site-urilor sursă în mod politicos (cu
          întârzieri, limite de pagini, cache). Întrucât rulezi aplicația local, pe propria
          răspundere, <strong>ești responsabil să respecți Termenii și Condițiile fiecărui site
          sursă</strong> pe care alegi să îl incluzi. Folosește aplicația pentru uz personal,
          pentru a-ți căuta o locuință.
        </p>
      </LegalSection>

      <LegalSection title="Licență (cod open-source)">
        <p>
          Codul este publicat sub licența Apache 2.0 — îl poți folosi, modifica și redistribui în
          condițiile acelei licențe. Codul este furnizat „ca atare", fără garanții.
        </p>
      </LegalSection>

      <LegalSection title="Limitarea răspunderii">
        <p>
          Aplicația este furnizată «ca atare», fără nicio garanție. Nu garantăm că toate anunțurile
          existente pe piață apar în rezultate, că datele extrase automat (preț, zonă, parcare,
          încălzire) sunt lipsite de erori, sau că aplicația funcționează neîntrerupt. Autorul nu
          răspunde pentru daune rezultate din utilizarea aplicației.
        </p>
      </LegalSection>

      <LegalSection title="Contact">
        <p>
          Întrebări, sugestii sau probleme: {CONTACT_EMAIL}. Legea aplicabilă: legea română.
        </p>
      </LegalSection>
    </LegalLayout>
  )
}
