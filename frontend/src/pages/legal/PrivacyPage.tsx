import { CONTACT_EMAIL, OPERATOR } from '@/lib/site'
import { LegalLayout, LegalList, LegalSection } from './LegalLayout'

export function PrivacyPage() {
  return (
    <LegalLayout title="Politica de confidențialitate">
      <LegalSection title="Cine suntem">
        <p>
          RentForYou (denumit în continuare «Serviciul») este operat de {OPERATOR}. Contact pentru
          orice întrebare legată de datele personale: {CONTACT_EMAIL}. Serviciul agregă anunțuri
          publice de închiriere din România și oferă funcții de căutare și filtrare.
        </p>
      </LegalSection>

      <LegalSection title="Ce date prelucrăm">
        <LegalList
          items={[
            <>
              Date de cont: adresa de email și parola (stocată exclusiv sub formă de hash bcrypt —
              nu putem vedea parola).
            </>,
            <>
              Autentificare Google: dacă alegi «Continuă cu Google», primim de la Google adresa de
              email verificată. Nu primim și nu stocăm parola contului Google.
            </>,
            <>
              Date de plată: plățile sunt procesate integral de Stripe. Noi nu vedem și nu stocăm
              numărul cardului — păstrăm doar identificatorul de client Stripe, statusul
              abonamentului și data de expirare a perioadei plătite.
            </>,
            <>
              Date tehnice: adresa IP este folosită temporar (în memorie) pentru limitarea
              abuzurilor (rate limiting) și în jurnalele serverului pentru securitate.
            </>,
            <>Cookie de sesiune: un singur cookie esențial (rs_session) care te ține autentificat.</>,
          ]}
        />
      </LegalSection>

      <LegalSection title="În ce scopuri și pe ce temei">
        <LegalList
          items={[
            <>
              Crearea și administrarea contului — executarea contractului (art. 6 alin. 1 lit. b
              GDPR).
            </>,
            <>
              Procesarea abonamentului — executarea contractului și obligații legale de facturare
              (lit. b și c).
            </>,
            <>Securitate, prevenirea abuzurilor — interes legitim (lit. f).</>,
            <>
              Anunțurile afișate provin din surse publice (site-uri de imobiliare) și pot conține
              date publicate de autorii anunțurilor; le indexăm pe temeiul interesului legitim, iar
              fiecare anunț trimite către sursa originală.
            </>,
          ]}
        />
      </LegalSection>

      <LegalSection title="Cui transmitem date">
        <LegalList
          items={[
            <>Stripe Payments Europe Ltd. — procesator de plăți (vezi politica lor de confidențialitate).</>,
            <>Google LLC — doar dacă folosești autentificarea Google.</>,
            <>Furnizorul de găzduire al serverului (UE).</>,
            <>Nu vindem și nu închiriem datele tale nimănui.</>,
          ]}
        />
      </LegalSection>

      <LegalSection title="Cât timp păstrăm datele">
        <p>
          Datele contului: până la ștergerea contului. Poți șterge contul oricând din meniul de
          cont («Șterge contul») — ștergerea anulează automat abonamentul și elimină datele tale.
          Documentele de facturare se păstrează conform obligațiilor fiscale legale.
        </p>
      </LegalSection>

      <LegalSection title="Drepturile tale">
        <p>
          Ai dreptul de acces, rectificare, ștergere, restricționare, portabilitate și opoziție,
          precum și dreptul de a depune o plângere la Autoritatea Națională de Supraveghere a
          Prelucrării Datelor cu Caracter Personal (ANSPDCP — dataprotection.ro). Pentru
          exercitarea drepturilor scrie-ne la {CONTACT_EMAIL}; răspundem în cel mult 30 de zile.
        </p>
      </LegalSection>
    </LegalLayout>
  )
}
